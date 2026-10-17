#!/usr/bin/env python3
"""Focused final review: stock scheduler, shared runtime RAM and boot handoff.

CPU-only: UART/socket/MMIO and flash programming are synthetic. This is not
a whole-device boot or a physical flash/recovery test.
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import sys
import unittest

from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.mips_const import *

import test_target as http
from test_uart_console import Console, physical

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'releases/v0.1.1-experimental-uart'
IMAGE = (RELEASE / 'SwitchLens-SG1218MPE-V5-v0.1.1-experimental-uart.bin').read_bytes()
MANIFEST = json.loads((RELEASE / 'build-manifest.json').read_text())
DUMP = (ROOT / 'backups/original/2026-10-17/GD25Q16B-xgpro-original.bin').read_bytes()
assert hashlib.sha256(DUMP).hexdigest() == 'b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87'
assert hashlib.sha256(IMAGE).hexdigest() == '27e4fce8d5c0c2999a324341cea7e96e37b1c0561e8d6a3218705b32b7aeee71'


def register_console(c):
    c.call(0xbfc2df00)  # clear the stock callback tables
    c.uc.reg_write(UC_MIPS_REG_A1, 0)
    c.uc.reg_write(UC_MIPS_REG_A2, 0xbfc2dec8)
    c.call(0xbfc2df70)  # register UART in entry 0, as runtime file 0x26988


def scheduler(c):
    c.uc.reg_write(UC_MIPS_REG_A1, 1)
    c.uc.reg_write(UC_MIPS_REG_A2, 0)
    c.call(0xbfc2df8c)  # same arguments as the main loop at file 0x26a50


class BootPath:
    """Execute original SPI 0x1898..0x19f8 and its actual CRC routine.

Mock flash identification, mode-setting, copy helper and diagnostic printing;
stop at runtime entry, before any runtime instruction executes.
"""
    RETURN = 0xbfc07ff0

    def __init__(self, staged):
        self.uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_BIG_ENDIAN)
        self.uc.ctl_set_cpu_model(UC_CPU_MIPS32_24KF)
        for address, size in [(0x1fc00000, 0x200000), (0x1f000000, 0x20000),
                              (0x14000000, 0x200000)]:
            self.uc.mem_map(address, size)
        self.uc.mem_write(0x1fc00000, DUMP[:0x200000])
        self.uc.mem_write(0x14000000, DUMP[:0x200000])
        # Bootstrap copies from SPI 0x690 and 0xca0, witnessed at 0x5c4..0x654.
        self.uc.mem_write(0x1f000400, DUMP[0x690:0xca0])
        self.uc.mem_write(0x1f0025a8, DUMP[0xca0:0x1a00])
        self.uc.mem_write(0x14008000, b'\0' * 16)  # state after web upgrade
        self.uc.mem_write(0x14100000, staged)
        self.copies = []
        self.mode_calls = []
        self.entered_runtime = False
        for addr in (0xbfc027d4, 0xbf00272c, 0xbf002a90, 0xbf0030c8, 0xb4008010):
            self.uc.hook_add(UC_HOOK_CODE, self.boundary, begin=addr, end=addr)

    def boundary(self, uc, address, size, unused):
        if address == 0xb4008010:
            self.entered_runtime = True
            uc.emu_stop()
            return
        if address == 0xbf002a90:
            self.mode_calls.append([uc.reg_read(r) for r in
                                    (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2)])
        if address == 0xbf0030c8:
            src, dest, length = [uc.reg_read(r) for r in
                                 (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2)]
            assert src == 0xb4100000 and dest == 0xb4008000
            assert length == len(IMAGE)
            self.copies.append([hex(src), hex(dest), length])
            uc.mem_write(physical(dest), bytes(uc.mem_read(physical(src), length)))
        uc.reg_write(UC_MIPS_REG_V0, 0)
        uc.reg_write(UC_MIPS_REG_PC, uc.reg_read(UC_MIPS_REG_RA))

    def run(self):
        self.uc.reg_write(UC_MIPS_REG_SP, 0xbf01f800)
        self.uc.reg_write(UC_MIPS_REG_RA, self.RETURN)
        self.uc.emu_start(0xbf0031a0, self.RETURN, count=40000000)
        assert self.entered_runtime or self.uc.reg_read(UC_MIPS_REG_PC) == self.RETURN


class ReleasePaths(unittest.TestCase):
    def test_stock_scheduler_dispatches_console(self):
        c = Console(IMAGE, b'help\r')
        register_console(c)
        scheduler(c)
        self.assertIn(b'print online help', c.output)
        self.assertTrue(c.output.endswith(b'RTK# '))
        self.assertFalse(c.input)

    def test_http_and_console_share_runtime_ram(self):
        m = http.Machine(IMAGE, MANIFEST)
        http.SCHEMA = json.loads((ROOT / 'schema/stats.schema.json').read_text())
        c = Console.__new__(Console)
        c.uc, c.input, c.output, c.received = m.u, deque(), bytearray(), 0
        for addr in (0xbfc1063c, 0xbfc1060c, 0xbfc105d8):
            c.uc.hook_add(UC_HOOK_CODE, c.serial, begin=addr, end=addr)
        c.call(0xbfc2de90)
        register_console(c)
        for _ in range(3):
            c.input.extend(b'help\r')
            scheduler(c)
            self.assertTrue(c.output.endswith(b'RTK# '))
            m.output.clear()
            self.assertEqual(m.run(), 0)
            self.assertEqual(len(m.document()['ports']), 18)

    def test_boot_accepts_staging_and_reaches_runtime_entry(self):
        b = BootPath(IMAGE)
        b.run()
        self.assertTrue(b.entered_runtime)
        self.assertEqual(b.copies, [['0xb4100000', '0xb4008000', len(IMAGE)]])
        self.assertEqual(b.mode_calls, [[0, 8, 255]])
        self.assertEqual(bytes(b.uc.mem_read(0x14008000, len(IMAGE))), IMAGE)
        self.assertEqual(bytes(b.uc.mem_read(0x14000000, 0x8000)), DUMP[:0x8000])
        self.assertEqual(bytes(b.uc.mem_read(0x141fc000, 0x4000)), DUMP[0x1fc000:0x200000])

    def test_boot_rejects_corrupted_staging_without_copy(self):
        corrupt = bytearray(IMAGE)
        corrupt[0x30000] ^= 1
        b = BootPath(bytes(corrupt))
        b.run()
        self.assertFalse(b.entered_runtime)
        self.assertFalse(b.copies)
        self.assertFalse(b.mode_calls)
        self.assertEqual(b.uc.reg_read(UC_MIPS_REG_V0), 1)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReleasePaths))
    summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'image_sha256': hashlib.sha256(IMAGE).hexdigest(),
               'scope': 'Stock scheduler; sequential CLI/HTTP in shared synthetic RAM; boot staging CRC and runtime handoff with mocked flash operations. No whole-device or hardware validation.'}
    out = ROOT / 'build-final-check'
    out.mkdir(exist_ok=True)
    (out / 'release-path-test-results.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    sys.exit(not result.wasSuccessful())
