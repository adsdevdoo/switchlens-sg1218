#!/usr/bin/env python3
"""Run the new BIN's stock CLI/controller and added hooks. No device I/O."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
from unicorn import UC_PROT_READ, UC_PROT_EXEC
from test_uart_console import Console
from test_board_signals import put, get, call
import test_target as http

ROOT = Path(__file__).resolve().parents[1]
STATE, TICKS, DATA = 0xbf014840, 0xbf002e94, 0xb800350c
TAG, MASK, BIT = 0xd4000000, 0xffffff, 1 << 27


def machine(command=b'', state=1, ticks=1000):
    c = Console(IMAGE, command)
    c.uc.mem_map(0x18003000, 0x1000)
    put(c, 0xb8003508, 0x39000000)
    put(c, DATA, 0x39780000)
    put(c, STATE, state)
    put(c, TICKS, ticks)
    put(c, 0xbf0143e4, 1)
    put(c, 0xbf0143e8, 16)
    c.uc.mem_protect(0x1fc00000, 0x200000, UC_PROT_READ | UC_PROT_EXEC)
    return c


def send(c, command):
    c.input.extend(command.encode()+b'\r')
    before = len(c.output)
    c.dispatch()
    return bytes(c.output[before:])


def power(c, value):
    c.uc.mem_write(0x1f0143e0 + 48 * 16 + 10, struct.pack('>h', value))


class CoolingTests(unittest.TestCase):
    def test_help_short_commands_and_status_no_writes(self):
        c = machine()
        for command in ['help', '?', 'help cool', 'cool', 'cool status']:
            text = send(c, command)
            self.assertIn(b'cool', text)
            self.assertEqual(get(c, DATA), 0x39780000)
            self.assertEqual(get(c, STATE), 1)
        self.assertIn(b'gpio26=0 gpio27=1', text)
        self.assertIn(b'mode=auto', text)

    def test_hold_both_levels_against_original_controller_and_return(self):
        for initial in (0, 1):
            for level in (0, 1):
                for load in (0, 1459, 1460, 1500, 1501, 2500):
                    with self.subTest(initial=initial, level=level, load=load):
                        c = machine(state=initial)
                        power(c, load)
                        self.assertIn(b'for 100 raw ticks', send(c, f'cool test {level}'))
                        packed = TAG | initial << 25 | level << 24 | 1000
                        expected_data = (0x39780000 & ~BIT) | level << 27
                        self.assertEqual(get(c, STATE), packed)
                        self.assertEqual(get(c, DATA), expected_data)
                        put(c, TICKS, 1099)
                        call(c, 0xbfc5c368)
                        self.assertEqual(get(c, STATE), packed)
                        self.assertEqual(get(c, DATA), expected_data)
                        self.assertEqual(get(c, 0xbf014400), load)
                        put(c, TICKS, 1100)
                        call(c, 0xbfc5c368)
                        expected = 1 if load < 1460 else 0 if load >= 1501 else initial
                        self.assertEqual(get(c, STATE), expected)
                        self.assertEqual(get(c, DATA), (0x39780000 & ~BIT) | expected << 27)

    def test_timeout_without_uart_input_and_tick_wrap(self):
        for start in (0, 0xfffff0, 0xfffffff0):
            c = machine(ticks=start)
            send(c, 'cool test 0')
            put(c, TICKS, (start+99) & 0xffffffff)
            c.dispatch()
            self.assertEqual((get(c, DATA)>>27)&1, 0)
            put(c, TICKS, (start+100) & 0xffffffff)
            c.dispatch()
            self.assertEqual(get(c, STATE), 1)
            self.assertEqual(get(c, DATA), 0x39780000)

    def test_stock_scheduler_expires_test_and_preserves_new_unrelated_bits(self):
        from test_release_paths import register_console, scheduler
        c = machine(b'cool test 0\r')
        register_console(c)
        scheduler(c)
        self.assertEqual(get(c, DATA), 0x31780000)
        # Other device activity changes a non-GPIO27 bit during the test.
        put(c, DATA, 0x31780008)
        put(c, TICKS, 1100)
        scheduler(c)
        self.assertEqual(get(c, STATE), 1)
        self.assertEqual(get(c, DATA), 0x39780008)

    def test_auto_recomputes_load_and_retrigger_cannot_extend(self):
        c = machine()
        send(c, 'cool test 0')
        packed = get(c, STATE)
        put(c, TICKS, 1010)
        self.assertIn(b'already active', send(c, 'cool test 1'))
        self.assertEqual(get(c, STATE), packed)
        power(c, 2500)
        self.assertIn(b'cool: auto', send(c, 'cool auto'))
        self.assertEqual(get(c, STATE), 0)
        self.assertEqual((get(c, DATA)>>27)&1, 0)
        self.assertEqual(get(c, 0xbf014400), 2500)

    def test_reject_invalid_commands_state_mux_direction(self):
        for cmd in ['cool test', 'cool test 2', 'cool test -1', 'cool test 00', 'cool test 0 extra', 'cool statu']:
            c = machine()
            send(c, cmd)
            self.assertEqual(get(c, STATE), 1)
            self.assertEqual(get(c, DATA), 0x39780000)
        for address, value in [(STATE, 2), (0xb8003500, BIT), (0xb8003508, 0)]:
            c = machine()
            put(c, address, value)
            state = get(c, STATE)
            self.assertIn(b'unchanged', send(c, 'cool test 0'))
            self.assertEqual(get(c, STATE), state)
            self.assertEqual(get(c, DATA), 0x39780000)

    def test_reg_missing_argument_unaligned_overflow_and_bounds(self):
        for cmd in ['reg', 'reg flashget 0x1', 'reg flashget 0x14840',
                    'reg socget 0x350cXYZ', 'reg socget -4',
                    'reg socget 0x350b', 'reg socget 0x10000350c',
                    'reg socset 0x350c', 'reg flashget 0x20000 0',
                    'reg flashget 0x1fffc 2', 'reg flashget 0x14840 65',
                    'reg socset 0x350c 0x100000000', 'reg socget 0x350c extra']:
            c = machine()
            self.assertIn(b'reg: rejected', send(c, cmd), cmd)
            self.assertEqual(get(c, DATA), 0x39780000)
            self.assertEqual(get(c, STATE), 1)

    def test_reg_valid_reads_and_writes_guarded_during_test(self):
        c = machine()
        self.assertIn(b'get socreg 0xb800350c = 0x39780000', send(c, 'reg socget 0x350c'))
        self.assertIn(b'set flashreg 0xbf014840 = 0x1', send(c, 'reg flashget 0x14840 0'))
        send(c, 'cool test 0')
        packed = get(c, STATE)
        self.assertIn(b'writes blocked', send(c, 'reg socset 0x350c 0'))
        self.assertEqual(get(c, STATE), packed)
        self.assertEqual(get(c, DATA), 0x31780000)
        send(c, 'cool auto')
        self.assertIn(b'set socreg', send(c, 'reg socset 0x350c 0x39780000'))

    def test_http_diagnostics_read_only_even_after_deadline(self):
        for state, now, mode, remaining in [(1, 100, 'auto', 0),
                (TAG | 1 << 25 | 100, 123, 'test', 77),
                (TAG | 100, 200, 'expired', 0), (2, 200, 'invalid', 0)]:
            m = http.Machine(IMAGE, MANIFEST)
            m.word(STATE, state)
            m.word(TICKS, now)
            m.word(0xb8003508, 0x39000000)
            m.word(DATA, 0x39780000)
            self.assertEqual(m.run(), 0)
            d = m.document()['cooling']
            self.assertEqual(d['mode'], mode)
            self.assertEqual(d['remaining_ticks'], remaining)
            self.assertEqual(d['test_limit_ticks'], 100)
            self.assertEqual(d['controller_state_raw'], state)
            self.assertEqual(d['gpio27_level'], 1)
            self.assertEqual(d['gpio26_level'], 0)
            self.assertIsNone(d['fan_rpm'])
            self.assertIsNone(d['fan_status'])
            self.assertEqual(m.load(STATE, 4), struct.pack('>I', state))
            self.assertEqual(m.load(DATA, 4), struct.pack('>I', 0x39780000))

    def test_stock_hysteresis_with_no_override(self):
        for state in (0, 1):
            for load in (0, 1459, 1460, 1500, 1501, 2500):
                c = machine(state=state)
                power(c, load)
                call(c, 0xbfc5c368)
                expected = 1 if load < 1460 else 0 if load >= 1501 else state
                self.assertEqual(get(c, STATE), expected)
                self.assertEqual(get(c, 0xbf014400), load)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build-cooling')
    args = p.parse_args()
    IMAGE = (args.build/'SwitchLens-SG1218MPE-V5-experimental.bin').read_bytes()
    MANIFEST = json.loads((args.build/'manifest.json').read_text())
    http.SCHEMA = json.loads((ROOT/'schema/stats.schema.json').read_text())
    run = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CoolingTests))
    result = dict(tests=run.testsRun, failures=len(run.failures), errors=len(run.errors),
                  image_sha256=hashlib.sha256(IMAGE).hexdigest(),
                  scope='Actual MIPS CLI/controller/HTTP instructions; synthetic UART/GPIO/ticks/PoE. No hardware test.')
    (args.build/'cooling-test-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    sys.exit(not run.wasSuccessful())
