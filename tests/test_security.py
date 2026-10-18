#!/usr/bin/env python3
"""Offline MIPS service-disable checks; no network or physical flash access."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

from unicorn import UC_HOOK_MEM_WRITE
from unicorn.mips_const import UC_MIPS_REG_PC, UC_MIPS_REG_S0, UC_MIPS_REG_SP

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_cooling_paths import call, get, machine, put, stub
import build_firmware as builder


def traps(c, hits):
    for addr, label in ((0xbfc38780, 'socket'), (0xbfc38b3c, 'bind'),
                        (0xbf01ca4c, 'send'), (0xbfc52edc, 'factory-write'),
                        (0xbfc543a4, 'credential-get')):
        stub(c, addr, lambda a, label=label: hits.append((label, a[:3])))


class SecurityTests(unittest.TestCase):
    def test_stock_initializers_bind_expected_udp_ports(self):
        for address, port in ((0xbfc47cf0, 29808), (0xbfc4d6f8, 1040)):
            c, hits = machine(STOCK), []
            traps(c, hits)
            call(c, address)
            self.assertEqual([a[2] for label, a in hits if label == 'bind'], [port])
            self.assertEqual([a[:2] for label, a in hits if label == 'socket'], [[4, 17]])

    def test_disabled_initializers_have_no_side_effects(self):
        for address in (0xbfc47cf0, 0xbfc4d668, 0xbfc4d6f8):
            c, hits = machine(IMAGE), []
            traps(c, hits)
            before = bytes(c.uc.mem_read(0x1f000400, 0x1e000))
            call(c, address)
            self.assertFalse(hits)
            # Wrapper uses the ordinary stack; global RAM remains unchanged.
            self.assertEqual(bytes(c.uc.mem_read(0x1f000400, 0x1e000)), before)

    def test_receive_callbacks_return_without_reading_unmapped_input(self):
        for address in (0xbfc48db0, 0xbfc4e238):
            for state in (0, 1, 2, 3):
                c, hits, writes = machine(IMAGE), [], []
                traps(c, hits)
                put(c, 0xbf0015c0, state)
                c.uc.hook_add(UC_HOOK_MEM_WRITE, lambda *a: writes.append(a[2]))
                call(c, address, 0, 0x10000000, 4096, 0x10000000)
                self.assertFalse(hits)
                self.assertFalse(writes)
                self.assertEqual(get(c, 0xbf0015c0), state)

    def test_boot_service_segment_preserves_http_and_continues(self):
        for signcheck in (0, 1):
            c, hits, http = machine(IMAGE), [], []
            traps(c, hits)
            stub(c, 0xbfc3b568, lambda a: http.append(True))
            stub(c, 0xbfc11514)  # diagnostic printing
            c.uc.reg_write(UC_MIPS_REG_SP, 0xbf01f600)
            c.uc.reg_write(UC_MIPS_REG_S0, signcheck)
            c.uc.emu_start(0xbfc2e64c, 0xbfc2e684, count=10000)
            self.assertEqual(c.uc.reg_read(UC_MIPS_REG_PC), 0xbfc2e684)
            self.assertEqual(c.uc.reg_read(UC_MIPS_REG_SP), 0xbf01f600)
            self.assertEqual(len(http), signcheck)
            self.assertFalse(hits)

    def test_security_boundaries_and_old_release_delta(self):
        # Independently review unchanged HTTP auth, codec and configuration tail.
        for start, end in ((0x33740, 0x33804), (0x34e50, 0x34f58),
                           (0x378e0, 0x37c18), (0x3fc38, 0x3fcf0),
                           (0xcb2e8, 0xcb3e8), (builder.END, len(IMAGE))):
            self.assertEqual(IMAGE[start:end], STOCK[start:end])
        allowed = [(0, 4), (builder.START, builder.END), (0x34e48, 0x34e50), (0x3425c, 0x34260), (0x34280, 0x34284), (0x24bb4, 0x24bb8), (0x25848, 0x2584c), (0x25ee4, 0x25ee8), (0x54344, 0x5434c)]
        allowed += [(offset, offset+8) for offset, _, _ in builder.DISABLED_SERVICES]
        allowed += [(offset, offset+len(before)+1) for offset, before, _ in builder.SERVICE_LOGS]
        changed = [i for i, (a, b) in enumerate(zip(PREVIOUS, IMAGE)) if a != b]
        self.assertTrue(changed)
        self.assertEqual(len(PREVIOUS), len(IMAGE))
        self.assertTrue(all(any(start <= i < end for start, end in allowed) for i in changed))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    args = p.parse_args()
    STOCK = (ROOT/'vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin').read_bytes()
    PREVIOUS = (ROOT/'releases/v0.1.4/SwitchLens-SG1218MPE-V5-v0.1.4.bin').read_bytes()
    IMAGE = (args.build/'SwitchLens-SG1218MPE-V5-experimental.bin').read_bytes()
    assert builder.sha(STOCK) == builder.EXPECTED
    assert builder.sha(PREVIOUS) == '4093f2e0dfcbbbc1c0caf0ed1d9d8902de747aa41e9525840b4755004e791b93'
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SecurityTests))
    report = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  image_sha256=hashlib.sha256(IMAGE).hexdigest(),
                  scope='MIPS initializers, receive entry points and boot service segment; mocked sockets; no whole-device or LAN reachability test')
    (args.build/'security-test-results.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    sys.exit(not result.wasSuccessful())
