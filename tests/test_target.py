#!/usr/bin/env python3
"""Execute patched MIPS plus original HTTP/router code with synthetic RAM/MMIO.

The socket boundary is mocked. No bootloader, IRQ, DMA, PoE hardware or real TCP
is emulated. Never opens a network connection or writes a device.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

import jsonschema
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_BIG_ENDIAN
from unicorn import UC_HOOK_CODE, UC_HOOK_BLOCK, UC_PROT_READ, UC_PROT_EXEC
from unicorn.mips_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import build_firmware as builder

RETURN = 0xbfcff800
REQUEST = 0x01000000
PATH = 0x01001000
INITIAL_SP = 0xbf01f600


def physical(a):
    return a & 0x1fffffff if 0x80000000 <= a < 0xc0000000 else a


class Machine:
    def __init__(self, image, manifest):
        self.u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_BIG_ENDIAN)
        self.u.ctl_set_cpu_model(UC_CPU_MIPS32_24KF)
        for base, size in [(0x1fc00000, 0x200000), (0x1f000000, 0x20000),
                           (0x01000000, 0x10000), (0x1b000000, 0x10000),
                           (0x141f0000, 0x10000), (0x18003000, 0x1000)]:
            self.u.mem_map(base, size)
        self.put(0xbfc08000, image)
        self.put(0xbf000400, image[0x720:0x3160])
        self.put(0xbf019528, image[0x3160:0x8178])
        self.symbols = {k: int(v, 16) for k, v in manifest['symbols'].items()}
        self.output = bytearray()
        self.sent = 0
        self.send_fail = None
        self.expire_on_send = False
        self.read_fail = set()
        self.unstable = False
        self.high_reads = 0
        self.entered = []
        self.min_sp = INITIAL_SP
        self.writes = set()
        self.setup()
        self.u.hook_add(UC_HOOK_CODE, self.intercept, begin=0xbfc38a64, end=0xbfc38a64)
        self.u.hook_add(UC_HOOK_CODE, self.read_register, begin=0xbfc10768, end=0xbfc10768)
        for address in [0xbfc4163c, 0xbfc3fc18, self.symbols['sg_http_entry']]:
            self.u.hook_add(UC_HOOK_CODE, self.destination, begin=address, end=address)
        self.u.hook_add(UC_HOOK_BLOCK, self.block)
        # Unicorn 2.1.4's MIPS MEM_WRITE hook faults on a store in a branch delay
        # slot. Enforce read-only flash/MMIO instead and compare all SRAM bytes.
        for address, size in [(0x1fc00000, 0x200000), (0x1b000000, 0x10000),
                              (0x141f0000, 0x10000), (0x01000000, 0x10000), (0x18003000, 0x1000)]:
            self.u.mem_protect(address, size, UC_PROT_READ | UC_PROT_EXEC)

    def put(self, address, data):
        self.u.mem_write(physical(address), bytes(data))

    def word(self, address, value):
        self.put(address, struct.pack('>I', value & 0xffffffff))

    def half(self, address, value):
        self.put(address, struct.pack('>H', value & 0xffff))

    def load(self, address, size):
        return bytes(self.u.mem_read(physical(address), size))

    def setup(self):
        # Boot registration at file302ac..302f8 -> BF00ECCC, file2b840.
        for i, pointer in enumerate([0xbfc10f08, 0xbf01a23c, 0xbf01a210,
                                     0xbf01a264, 0xbfc38040, 0xbfc38518]):
            self.word(0xbf00eccc+4*i, pointer)
        self.put(0xbf0015f0, b'\1')
        self.put(0xbf0015fc, 'Lab "A"\\\nпорт'.encode()+b'\0')
        self.put(0xbf014348, b'1.0.0 Build 20230616 Rel.57668\0')
        self.put(0xbf016d3a, bytes([192, 0, 2, 10, 255, 255, 255, 0, 192, 0, 2, 1]))
        self.word(0xbf002e90, 0xfffffffe)
        self.word(0xbf002e94, 123)
        self.word(0xbf0143e0, 16)
        self.word(0xbf0143f4, 2500)
        self.word(0xbf014400, 1205)
        self.put(0xbf002114, b'\1')
        self.word(0xbB00a9ec, 0x0211)
        self.word(0xbB00a9f0, 0x22334455)
        for offset in [0xa188, 0xa19c, 0xa1a0, 0xa1a4]:
            self.word(0xbb000000+offset, 0x0300ffff)
        self.word(0xbb00a190, 0xaaaaaaaa)
        self.word(0xbb00a194, 0xaaaaaaaa)
        for i in range(18):
            self.word(0xbf001658+4*i, 1)
            for offset in [0x64, 0x9e, 0x112]:
                self.put(0xbf001658+offset+i, b'\1')
            physical_port = i if i < 16 else i+8
            base = 0xbb001200+physical_port*256
            for offset in range(0, 0xc0, 4):
                self.word(base+offset, 10000*(i+1)+offset)
            self.word(base, 0xffffffff if i == 0 else i+1)
            self.word(base+4, 0xffffffff if i == 0 else 7+i)
            self.word(base+8, 0x200000+i)
            self.word(base+12, 9+i)
            if i < 16:
                p = 0xbf014408+48*i
                for offset, value in [(2, 1), (4, 330), (14, 241), (16, 500), (18, 121)]:
                    self.half(p+offset, value)
                self.word(p+8, 1)
                self.word(p+20, 300)
                self.word(p+24, 2)
                r = 0xbf002118+40*i
                self.put(r+8, f'192.0.2.{20+i}'.encode()+b'\0')
                for offset, value in [(24, 60), (28, 10), (32, 3), (36, 5)]:
                    self.word(r+offset, value)
                for offset, value in [(0, 2), (2, 4), (4, 100)]:
                    self.half(0xbf014774+6*i+offset, value)
        for offset, value in [(0xbf00e280, 1), (0xbf00e2a0, 2), (0xbf00e2a4, 4)]:
            self.word(offset, value)
        self.word(REQUEST, 0)
        self.word(REQUEST+4, 1)
        self.put(REQUEST+8, b'/stats.json\0')
        self.put(PATH, b'/stats.json\0')

    def ret(self, value):
        self.u.reg_write(UC_MIPS_REG_V0, value & 0xffffffff)
        self.u.reg_write(UC_MIPS_REG_PC, self.u.reg_read(UC_MIPS_REG_RA))

    def intercept(self, uc, address, size, user):
        self.sent += 1
        length = uc.reg_read(UC_MIPS_REG_A2)
        assert 0 < length <= 1460, length
        if self.sent == self.send_fail:
            self.ret(-1)
            return
        self.output += self.load(uc.reg_read(UC_MIPS_REG_A1), length)
        if self.expire_on_send:
            self.word(0xbf002e94, 164)
        self.ret(0)

    def read_register(self, uc, address, size, user):
        offset = uc.reg_read(UC_MIPS_REG_A1)
        assert uc.reg_read(UC_MIPS_REG_A0) == 0
        if offset in self.read_fail:
            self.ret(-1)
        elif self.unstable and offset == 0x1200:
            self.high_reads += 1
            self.word(uc.reg_read(UC_MIPS_REG_A2), self.high_reads)
            self.ret(0)
        # Other reads execute the original BFC10768 MMIO implementation.

    def destination(self, uc, address, size, user):
        self.entered.append(address)
        if address != self.symbols['sg_http_entry']:
            self.ret(0)

    def check_ram_changes(self, before):
        after = self.load(0xbf000000, 0x20000)
        allowed = [(0x1f01e540, 0x1f01f800), (0x1f010f8c, 0x1f011550)]
        if getattr(self, 'outer_request', False):
            allowed.append((0x1f011670, 0x1f011672))
        if self.expire_on_send:
            allowed.append((0x1f002e94, 0x1f002e98))  # synthetic IRQ tick injection
        for i, (a, b) in enumerate(zip(before, after)):
            if a == b:
                continue
            address = 0x1f000000+i
            assert any(lo <= address < hi for lo, hi in allowed), f'Unexpected SRAM change {address:#x}'
            self.writes.add(address)

    def block(self, uc, address, size, user):
        self.min_sp = min(self.min_sp, uc.reg_read(UC_MIPS_REG_SP))

    def run(self, function=None, path='/stats.json', method=1, sp=INITIAL_SP):
        self.put(PATH, path.encode()+b'\0')
        self.put(REQUEST+8, path.encode()+b'\0')
        self.word(REQUEST+4, method)
        u = self.u
        u.reg_write(UC_MIPS_REG_SP, sp)
        u.reg_write(UC_MIPS_REG_RA, RETURN)
        u.reg_write(UC_MIPS_REG_A0, REQUEST)
        u.reg_write(UC_MIPS_REG_A1, PATH)
        saved = [UC_MIPS_REG_S0, UC_MIPS_REG_S1, UC_MIPS_REG_S2, UC_MIPS_REG_S3,
                 UC_MIPS_REG_S4, UC_MIPS_REG_S5, UC_MIPS_REG_S6, UC_MIPS_REG_S7,
                 UC_MIPS_REG_FP, UC_MIPS_REG_GP]
        for i, reg in enumerate(saved):
            u.reg_write(reg, 0x12345600+i)
        address = self.symbols[function] if function else 0xbfc3b740
        before = self.load(0xbf000000, 0x20000)
        u.emu_start(address, RETURN, count=12000000)
        assert u.reg_read(UC_MIPS_REG_PC) == RETURN, 'Execution did not return within bound'
        assert u.reg_read(UC_MIPS_REG_SP) == sp, 'Stack pointer not restored'
        for i, reg in enumerate(saved):
            assert u.reg_read(reg) == 0x12345600+i, f'Callee-saved register {reg} clobbered'
        self.check_ram_changes(before)
        return u.reg_read(UC_MIPS_REG_V0)

    def document(self):
        headers, body = bytes(self.output).split(b'\r\n\r\n', 1)
        assert headers.startswith(b'HTTP/1.1 200 '), headers
        for header in [b'Content-Type: application/json', b'Cache-Control: no-store', b'Connection: close']:
            assert header in headers, headers
        data = json.loads(body)
        jsonschema.Draft202012Validator(SCHEMA).validate(data)
        return data


class TargetTests(unittest.TestCase):
    def new(self):
        return Machine(IMAGE, MANIFEST)

    def test_get_full_stock_router_and_http(self):
        m = self.new()
        self.assertEqual(m.run(), 0)
        d = m.document()
        self.assertEqual(d['system']['description'], 'Lab "A"\\\nпорт')
        self.assertEqual(d['system']['name'], d['system']['description'])
        self.assertEqual(d['system']['hardware_version'], 'TL-SG1218MPE 5.0')
        self.assertEqual(d['system']['firmware_version'], '1.0.0 Build 20230616 Rel.57668')
        self.assertEqual(d['system']['mac'], '02:11:22:33:44:55')
        self.assertEqual(d['system']['ip_address'], '192.0.2.10')
        self.assertEqual(d['system']['subnet_mask'], '255.255.255.0')
        self.assertEqual(d['system']['default_gateway'], '192.0.2.1')
        self.assertEqual(d['system']['uptime_ticks_raw'], 0xfffffffe)
        self.assertIsNone(d['system']['uptime_seconds'])
        self.assertEqual(d['poe']['consumption_w'], 120.5)
        self.assertEqual(d['poe']['remaining_w'], 129.5)
        for i, p in enumerate(d['ports']):
            self.assertEqual(p['port'], i+1)
            self.assertTrue(p['link_up'])
            self.assertEqual(p['speed_mbps'], 1000)
            self.assertEqual(p['speed_config_code'], 1)
            self.assertEqual(p['speed_actual_code'], 6)
            c = p['counters']
            self.assertEqual(c['rx_bytes'], str(2**64-1 if i == 0 else ((i+1)<<32)+7+i))
            self.assertEqual(c['tx_bytes'], str(((0x200000+i)<<32)+9+i))
            self.assertEqual(c['rx_good_packets'], str(30000*(i+1)+0x14+0x18+0x1c))
            self.assertEqual(c['tx_drop_packets'], str(10000*(i+1)+0x2c))
            self.assertEqual(c['rx_bridge_discards'], str(10000*(i+1)+0x10))
            self.assertEqual(c['rx_mac_discards'], str(10000*(i+1)+0xbc))
            self.assertIsNone(c['rx_discards'])
            self.assertIsNone(c['tx_packets_256_511'])
            if i >= 16:
                self.assertIsNone(p['poe'])
                continue
            self.assertEqual(p['poe']['power_w'], 12.1)
            self.assertEqual(p['poe']['voltage_v'], 50)
            self.assertEqual(p['poe']['current_ma'], 241)
            self.assertEqual(p['poe']['pd_class'], 4)
            self.assertEqual(p['poe']['status'], 'ON')
            self.assertIsNone(p['poe']['power_limit_w'])
            rec = p['poe']['recovery']
            self.assertEqual(rec['ping_address'], f'192.0.2.{20+i}')
            self.assertEqual([rec[k] for k in ['startup_delay_seconds', 'interval_seconds',
                'failure_threshold', 'break_seconds', 'failures_current', 'reboots_raw', 'pings_raw']],
                [60, 10, 3, 5, 2, 4, 100])
        RESULT.update(response_bytes=len(m.output), socket_calls=m.sent,
                      observed_stack_bytes=INITIAL_SP-m.min_sp,
                      min_sp=hex(m.min_sp), permitted_write_locations=len(m.writes))
        if OUTPUT:
            OUTPUT.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n')

    def test_stock_statistics_route_is_preserved(self):
        m = self.new()
        self.assertEqual(m.run(path='/PortStatisticsRpm.htm'), 0)
        self.assertEqual(m.entered, [0xbfc4163c])
        self.assertFalse(m.output)

    def test_flash_config_fallback_and_poE_invalid_readings(self):
        m = self.new()
        for ram, flash, size in [(0xbf0015fc, 0xb41fe008, 33),
                                 (0xbf001658, 0xb41fe064, 0x15c),
                                 (0xbf002110, 0xb41feb1c, 0x288)]:
            m.put(flash, m.load(ram, size))
        m.put(0xbf0015f0, b'\0')
        m.half(0xbf014408+18, -1)
        m.half(0xbf014408+14, 0)
        m.word(0xbf014408+24, 99)
        m.word(0xbf014400, 3000)
        self.assertEqual(m.run(), 0)
        d = m.document()
        self.assertEqual(d['system']['description'], 'Lab "A"\\\nпорт')
        self.assertTrue(d['ports'][0]['admin_enabled'])
        self.assertIsNone(d['ports'][0]['poe']['power_w'])
        self.assertIsNone(d['ports'][0]['poe']['current_ma'])
        self.assertIsNone(d['ports'][0]['poe']['status'])
        self.assertEqual(d['ports'][0]['poe']['status_code'], 99)
        self.assertEqual(d['poe']['remaining_w'], 0)
        self.assertEqual(d['poe']['consumption_w'], 300)
        self.assertEqual(d['ports'][15]['poe']['recovery']['ping_address'], '192.0.2.35')

    def test_session_check_precedes_json(self):
        m = self.new()
        m.word(0xbf011660, 1)
        m.put(0xbf001488, b'synthetic-session\0')
        self.assertEqual(m.run(), 0)
        self.assertEqual(m.entered, [0xbfc3fc18])
        self.assertFalse(m.output)
        m.output.clear()
        m.put(REQUEST+0xec, b'synthetic-session\0')
        self.assertEqual(m.run(), 0)
        m.document()

    def test_outer_client_ip_and_inner_cookie_checks(self):
        # Enter the actual caller, not just the internal route dispatch tested
        # by v0.1.3. Its client-IP gate can substitute the Unauth route first.
        for active, cookie, same_ip, allowed in [
                (1, True, True, True), (1, False, True, False),
                (1, True, False, False), (0, False, True, False)]:
            with self.subTest(active=active,cookie=cookie,same_ip=same_ip):
                m = self.new()
                m.outer_request = True
                m.symbols['stock_http_outer'] = 0xbfc3ce48
                m.word(REQUEST+0x8c, PATH)
                m.word(0xbf011660, active)
                m.put(0xbf001488, b'synthetic-session\0')
                m.put(REQUEST+0xec, b'synthetic-session\0' if cookie else b'wrong-session\0')
                m.put(0xbf018df4, bytes([192,0,2,20]))
                m.put(REQUEST+0x298, bytes([192,0,2,20 if same_ip else 21]))
                m.run(function='stock_http_outer')
                if allowed:
                    m.document()
                else:
                    self.assertNotIn(m.symbols['sg_http_entry'], m.entered)
                    self.assertFalse(m.output)

    def test_post_and_near_matches_do_not_call_json(self):
        for path, method in [('/stats.json', 2), ('/stats.jsonx', 1),
                             ('/stats.json/', 1), ('/Stats.json', 1), ('/stats.json?x', 1)]:
            with self.subTest(path=path, method=method):
                m = self.new()
                m.run(path=path, method=method)
                self.assertNotIn(m.symbols['sg_http_entry'], m.entered)

    def test_register_failure_and_unstable_counter_become_null(self):
        m = self.new()
        m.read_fail = {0xa9ec, 0xa188, 0x1208}
        m.unstable = True
        self.assertEqual(m.run(), 0)
        d = m.document()
        self.assertIsNone(d['system']['mac'])
        self.assertIsNone(d['ports'][0]['link_up'])
        self.assertIsNone(d['ports'][0]['counters']['rx_bytes'])
        self.assertIsNone(d['ports'][0]['counters']['tx_bytes'])
        self.assertEqual(m.high_reads, 6)

    def test_send_failure_stops_and_drops_tail(self):
        # Includes failure on final flush rather than only full buffers.
        baseline = self.new()
        self.assertEqual(baseline.run(), 0)
        for fail in [1, 3, baseline.sent]:
            with self.subTest(send=fail):
                m = self.new()
                m.send_fail = fail
                self.assertNotEqual(m.run(), 0)
                self.assertEqual(m.sent, fail)
                self.assertEqual(m.load(0xbf011540, 4), struct.pack('>I', 0xbf010f8c))

    def test_tick_budget_stops_stream(self):
        m = self.new()
        m.expire_on_send = True
        self.assertNotEqual(m.run(), 0)
        self.assertEqual(m.sent, 1)

    def test_stack_guard_and_wrong_port_count(self):
        m = self.new()
        self.assertEqual(m.run(function='sg_http_entry', sp=0xbf01f138), 0xffffffff)
        self.assertFalse(m.output)
        self.assertFalse(m.writes)
        m.word(0xbf0143e0, 8)
        self.assertEqual(m.run(), 0xffffffff)
        self.assertFalse(m.output)

    def test_image_integrity_and_fail_closed_builder(self):
        self.assertEqual(builder.sha(ORIGINAL), builder.EXPECTED)
        self.assertEqual(builder.sha(IMAGE), MANIFEST['output_sha256'])
        self.assertEqual(len(IMAGE), len(ORIGINAL))
        self.assertEqual(struct.unpack('>I', IMAGE[:4])[0], zlib.crc32(IMAGE[0x10:builder.END]))
        self.assertEqual(IMAGE[builder.END:], ORIGINAL[builder.END:])
        self.assertEqual(IMAGE[0x33740:0x33804], ORIGINAL[0x33740:0x33804])
        self.assertEqual(IMAGE[0x34e48:0x34f58], ORIGINAL[0x34e48:0x34f58])
        self.assertNotIn('sg_public_compare', MANIFEST['symbols'])
        syms = {k: int(v, 16) for k, v in MANIFEST['symbols'].items()}
        regenerated, _ = builder.package(ORIGINAL, PAYLOAD, syms, uart_cli=MANIFEST.get('uart_cli', False), cooling_cli=MANIFEST.get('cooling_cli', False))
        self.assertEqual(regenerated, IMAGE)
        for original, payload, symbols in [(b'bad', PAYLOAD, syms), (ORIGINAL, b'', syms),
                 (ORIGINAL, b'x'*(builder.END-builder.START+1), syms),
                 (ORIGINAL, PAYLOAD, dict(syms, sg_route_compare=0xbfc08000))]:
            with self.assertRaises(ValueError):
                builder.package(original, payload, symbols)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('original', type=Path)
    p.add_argument('--build', type=Path, default=ROOT/'build-target')
    p.add_argument('--synthetic-output', type=Path)
    args = p.parse_args()
    ORIGINAL = args.original.read_bytes()
    assert hashlib.sha256(ORIGINAL).hexdigest() == builder.EXPECTED
    IMAGE = (args.build/'SwitchLens-SG1218MPE-V5-experimental.bin').read_bytes()
    PAYLOAD = (args.build/'payload.bin').read_bytes()
    MANIFEST = json.loads((args.build/'manifest.json').read_text())
    SCHEMA = json.loads((ROOT/'schema/stats.schema.json').read_text())
    OUTPUT, RESULT = args.synthetic_output, {}
    run = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TargetTests))
    RESULT.update(tests=run.testsRun, failures=len(run.failures), errors=len(run.errors),
                  image_sha256=builder.sha(IMAGE), scope='CPU/HTTP emulation with mocked socket and synthetic MMIO; no hardware validation')
    (args.build/'target-test-results.json').write_text(json.dumps(RESULT, indent=2)+'\n')
    print(json.dumps(RESULT, indent=2))
    sys.exit(not run.wasSuccessful())
