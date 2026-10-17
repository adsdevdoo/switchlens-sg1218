#!/usr/bin/env python3
"""Execute original UART dispatcher/parser/help with a synthetic UART FIFO.

No device I/O. Tests establish CPU behavior, not physical RX or recovery.
"""
import argparse
from collections import deque
import json
from pathlib import Path
import sys
import unittest

from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_uart_diagnostic

RETURN = 0xbfcff800
STACK = 0xbf01f600


def physical(address):
    return address & 0x1fffffff if 0x80000000 <= address < 0xc0000000 else address


class Console:
    def __init__(self, image, incoming=b''):
        self.uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_BIG_ENDIAN)
        self.uc.ctl_set_cpu_model(UC_CPU_MIPS32_24KF)
        self.uc.mem_map(0x1fc00000, 0x200000)
        self.uc.mem_map(0x1f000000, 0x20000)
        self.uc.mem_write(0x1fc08000, image)
        self.uc.mem_write(0x1f000400, image[0x720:0x3160])
        self.uc.mem_write(0x1f019528, image[0x3160:0x8178])
        self.input = deque(incoming)
        self.output = bytearray()
        self.received = 0
        for addr in (0xbfc1063c, 0xbfc1060c, 0xbfc105d8):
            self.uc.hook_add(UC_HOOK_CODE, self.serial, begin=addr, end=addr)
        self.call(0xbfc2de90)  # stock command-permission initialization

    def serial(self, uc, address, size, unused):
        if address == 0xbfc1063c:
            value = bool(self.input)
        elif address == 0xbfc1060c:
            if not self.input:
                raise AssertionError('Blocking UART read without input')
            value = self.input.popleft()
            self.received += 1
        else:
            self.output.append(uc.reg_read(UC_MIPS_REG_A1) & 0xff)
            value = 0
        uc.reg_write(UC_MIPS_REG_V0, value)
        uc.reg_write(UC_MIPS_REG_PC, uc.reg_read(UC_MIPS_REG_RA))

    def call(self, address):
        self.uc.reg_write(UC_MIPS_REG_SP, STACK)
        self.uc.reg_write(UC_MIPS_REG_RA, RETURN)
        self.uc.reg_write(UC_MIPS_REG_A0, 0)
        self.uc.emu_start(address, RETURN, count=2000000)
        assert self.uc.reg_read(UC_MIPS_REG_PC) == RETURN, 'Instruction bound exceeded'
        assert self.uc.reg_read(UC_MIPS_REG_SP) == STACK, 'Stack not restored'

    def dispatch(self):
        self.call(0xbfc2dec8)


class ConsoleTests(unittest.TestCase):
    def test_stock_gate_ignores_enter(self):
        c = Console(STOCK, b'\r')
        c.dispatch()
        self.assertEqual(c.received, 0)
        self.assertEqual(c.output, b'')

    def test_diagnostic_prompts_without_input_and_returns(self):
        c = Console(PATCHED)
        c.dispatch()
        self.assertEqual(c.output, b'RTK# ')
        c.dispatch()
        self.assertEqual(c.output, b'RTK# ')

    def test_enter_cr_and_lf(self):
        for ending in (b'\r', b'\n', b'\r\n'):
            c = Console(PATCHED, ending)
            # The stock event callback returns after handling a line ending.
            # CRLF is consumed by two passes through the main event loop.
            for _ in ending:
                c.dispatch()
            self.assertEqual(c.received, len(ending))
            self.assertTrue(c.output.endswith(b'RTK# '), c.output)

    def test_help_and_alias(self):
        for command in (b'help\r', b'?\r'):
            c = Console(PATCHED, command)
            c.dispatch()
            self.assertEqual(c.received, len(command))
            self.assertIn(b'print online help', c.output)
            self.assertNotIn(b'is not enable', c.output)
            self.assertTrue(c.output.endswith(b'RTK# '), c.output)

    def test_unknown_command(self):
        c = Console(PATCHED, b'no_such_command\r')
        c.dispatch()
        self.assertIn(b'Unknown command', c.output)
        self.assertTrue(c.output.endswith(b'RTK# '))

    def test_diagnostic_delta_and_reproducibility(self):
        rebuilt, _, manifest = build_uart_diagnostic.build()
        self.assertEqual(rebuilt, PATCHED)
        self.assertTrue(manifest['uart_cli'])
        allowed = [(0, 4), (0x25e94, 0x25e98), (0x25ed8, 0x25edc)]
        changed = [i for i, (a, b) in enumerate(zip(BASE, PATCHED)) if a != b]
        self.assertEqual(len(BASE), len(PATCHED))
        self.assertTrue(changed)
        self.assertTrue(all(any(lo <= i < hi for lo, hi in allowed) for i in changed))
        self.assertEqual(PATCHED[0xf7018:0xf701c], b'\0' * 4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT / 'build-uart-diagnostic')
    args = parser.parse_args()
    STOCK = (ROOT / 'vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin').read_bytes()
    BASE = (ROOT / 'releases/v0.1.0-experimental/SwitchLens-SG1218MPE-V5-v0.1.0-experimental.bin').read_bytes()
    PATCHED = (args.build / build_uart_diagnostic.FILENAME).read_bytes()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConsoleTests))
    summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'image_sha256': build_uart_diagnostic.builder.sha(PATCHED),
               'scope': 'MIPS dispatcher/parser/help with mocked UART FIFO; no physical hardware or recovery test'}
    (args.build / 'uart-test-results.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    sys.exit(not result.wasSuccessful())
