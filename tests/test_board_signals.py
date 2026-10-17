#!/usr/bin/env python3
"""Execute original GPIO/PoE instructions and UART reads with synthetic hardware.

These tests establish code behavior, not the physical purpose of any GPIO.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_EXEC
from unicorn.mips_const import UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3
from unicorn.mips_const import UC_MIPS_REG_PC, UC_MIPS_REG_RA, UC_MIPS_REG_SP, UC_MIPS_REG_V0

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audit_cooling
from decode_board_signals import decode
from test_uart_console import Console, RETURN, STACK

IMAGE = (ROOT / 'releases/v0.1.1-experimental-uart/SwitchLens-SG1218MPE-V5-v0.1.1-experimental-uart.bin').read_bytes()
IMAGE_SHA = '27e4fce8d5c0c2999a324341cea7e96e37b1c0561e8d6a3218705b32b7aeee71'
assert hashlib.sha256(IMAGE).hexdigest() == IMAGE_SHA


def put(c, address, value):
    c.uc.mem_write(address & 0x1fffffff, struct.pack('>I', value))


def get(c, address):
    return struct.unpack('>I', c.uc.mem_read(address & 0x1fffffff, 4))[0]


def machine(command=b'', gpio=0):
    c = Console(IMAGE, command)
    c.uc.mem_map(0x18003000, 0x1000)
    put(c, 0xb800350c, gpio)
    put(c, 0xb8003508, 1 << 27)
    c.uc.mem_protect(0x1fc00000, 0x200000, UC_PROT_READ | UC_PROT_EXEC)
    return c


def call(c, address, a0=0):
    c.uc.reg_write(UC_MIPS_REG_SP, STACK)
    c.uc.reg_write(UC_MIPS_REG_RA, RETURN)
    c.uc.reg_write(UC_MIPS_REG_A0, a0)
    c.uc.emu_start(address, RETURN, count=100000)
    assert c.uc.reg_read(UC_MIPS_REG_PC) == RETURN
    assert c.uc.reg_read(UC_MIPS_REG_SP) == STACK


class BoardSignals(unittest.TestCase):
    def test_hysteresis_boundaries_and_preserve_other_gpio_bits(self):
        for state in (0, 1):
            for power in (0, 1459, 1460, 1500, 1501, 2500):
                with self.subTest(state=state, power=power):
                    c = machine(gpio=0xa5a55a5a)
                    put(c, 0xbf0143e4, 1)
                    put(c, 0xbf0143e8, 16)
                    # Last port verifies the inclusive range and 48-byte stride.
                    c.uc.mem_write(0x1f0143e0 + 48 * 16 + 10, struct.pack('>h', power))
                    put(c, 0xbf014840, state)
                    expected = 1 if power < 1460 else 0 if power >= 1501 else state
                    call(c, 0xbfc5c368)
                    self.assertEqual(get(c, 0xbf014400), power)
                    self.assertEqual(get(c, 0xbf014840), expected)
                    self.assertEqual(get(c, 0xb800350c), (0xa5a55a5a & ~(1 << 27)) | (expected << 27))

    def test_sum_and_hysteresis_history(self):
        c = machine()
        put(c, 0xbf0143e4, 1)
        put(c, 0xbf0143e8, 16)
        for power, expected in [(1459, 1), (1460, 1), (1500, 1), (1501, 0), (1500, 0), (1460, 0), (1459, 1)]:
            c.uc.mem_write(0x1f0143e0 + 48 + 10, struct.pack('>h', 700))
            c.uc.mem_write(0x1f0143e0 + 48 * 16 + 10, struct.pack('>h', power - 700))
            call(c, 0xbfc5c368)
            self.assertEqual(get(c, 0xbf014400), power)
            self.assertEqual(get(c, 0xbf014840), expected)

    def test_input_drives_led_modes_not_rpm(self):
        for enabled in (0, 1):
            for level in (0, 1):
                c = machine(gpio=level << 26)
                c.uc.mem_protect(0x18003000, 0x1000, UC_PROT_READ)
                calls = []

                def led(uc, address, size, unused):
                    calls.append((address, [uc.reg_read(r) for r in (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3)]))
                    uc.reg_write(UC_MIPS_REG_V0, 0)
                    uc.reg_write(UC_MIPS_REG_PC, uc.reg_read(UC_MIPS_REG_RA))

                for address in (0xbfc26828, 0xbfc26830):
                    c.uc.hook_add(UC_HOOK_CODE, led, begin=address, end=address)
                call(c, 0xbfc5e0a4, enabled)
                modes = [args for addr, args in calls if addr == 0xbfc26830]
                self.assertEqual(modes, [[0, 26, 0, 5 if enabled and level else 0],
                                         [0, 27, 0, 5 if enabled and not level else 0]])
                self.assertEqual(get(c, 0xb800350c), level << 26)

    def test_uart_read_syntax_and_read_only_access(self):
        commands = [
            (b'reg socget 0x3508\r', b'get socreg 0xb8003508 = 0x8000000'),
            (b'reg socget 0x350c\r', b'get socreg 0xb800350c = 0xc000000'),
            (b'reg flashget 0x14840 0\r', b'set flashreg 0xbf014840 = 0x1'),
        ]
        combined = []
        for command, expected in commands:
            c = machine(command, gpio=0x0c000000)
            put(c, 0xbf014840, 1)
            c.uc.mem_protect(0x18003000, 0x1000, UC_PROT_READ)
            c.uc.mem_protect(0x1f014000, 0x1000, UC_PROT_READ)
            c.dispatch()
            self.assertIn(expected, c.output)
            self.assertEqual(c.received, len(command))
            combined.append(c.output.decode())
        record = decode('\n'.join(combined))
        self.assertEqual(record['signals']['gpio26_level_raw'], 1)
        self.assertEqual(record['signals']['gpio27_level_raw'], 1)
        self.assertTrue(record['signals']['output_matches_state'])
        self.assertIsNone(record['fan_rpm'])
        self.assertIsNone(record['fan_status'])

    def test_documented_double_dash_is_not_accepted(self):
        c = machine(b'reg --socget 0x350c\r')
        c.dispatch()
        self.assertIn(b'realtek command usage:', c.output)
        self.assertNotIn(b'get socreg 0xb800350c =', c.output)

    def test_decoder_rejects_mixed_missing_and_oversized_results(self):
        text = 'get socreg 0xb8003508 = 0x8000000\nget socreg 0xb800350c = 0x8000000\nset flashreg 0xbf014840 = 0x1\n'
        for bad in (text + text, text.splitlines()[0], text.replace('= 0x1\n', '= 0x100000000\n'), text.replace('set flashreg', 'get socreg')):
            with self.assertRaises(ValueError):
                decode(bad)
        invalid = decode(text.replace('= 0x1\n', '= 0x2\n'))
        self.assertFalse(invalid['signals']['poe_load_control_state_valid'])
        self.assertIsNone(invalid['signals']['output_matches_state'])

    def test_audit_sha_gate(self):
        path = ROOT / 'vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin'
        original = path.read_bytes()
        record = audit_cooling.analyze(original)
        self.assertEqual(record['output_path']['hold_previous_state_raw_interval_inclusive'], [1460, 1500])
        for invalid in (b'', original[:-1], bytes([original[0] ^ 1]) + original[1:]):
            with self.assertRaises(ValueError):
                audit_cooling.analyze(invalid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BoardSignals))
    report = {'image_sha256': IMAGE_SHA, 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'scope': 'Original MIPS code with synthetic GPIO/PoE values and UART input; not hardware validation',
              'fan_mapping_verified': False}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    sys.exit(not result.wasSuccessful())
