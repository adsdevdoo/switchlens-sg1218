#!/usr/bin/env python3
"""Execute stock raw HTTP parser -> patched outer callback -> original response
writers + JSON. Network/IRQ/MMIO are synthetic; no hardware/real concurrency.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unicorn import UC_PROT_ALL, UC_PROT_READ, UC_PROT_EXEC, UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A2
import test_target as http

ROOT = Path(__file__).resolve().parents[1]
SESSION = [(0xbf001488, 100), (0xbf011660, 4), (0xbf011670, 2), (0xbf018df4, 4)]
ADMIN = ['/SystemInfoRpm.htm', '/ConfigRpm.htm', '/config_back.cgi',
         '/SystemRebootRpm.htm', '/SystemResetRpm.htm', '/fwupgradephase0.htm',
         '/PoeConfigRpm.htm', '/PortStatisticsRpm.htm', '/reboot.cgi',
         '/savingconfig.cgi', '/system_name_set.cgi', '/poe_global_config.cgi',
         '/poe_port_config.cgi', '/port_statistics_set.cgi']

class RawMachine(http.Machine):
    def __init__(self):
        super().__init__(IMAGE, MANIFEST)
        self.symbols.update(stock_parser=0xbf01d05c, stock_outer=0xbfc3ce48)
        self.auth_entries = []
        self.u.hook_add(UC_HOOK_CODE, lambda u,a,s,x: self.auth_entries.append(a),
                        begin=0xbfc3ce50, end=0xbfc3ce50)
        self.u.hook_add(UC_HOOK_CODE, lambda u,a,s,x: self.auth_entries.append(a),
                        begin=0xbfc3b740, end=0xbfc3b740)
        self.set_session(1)

    def set_session(self, active):
        self.word(0xbf011660, active)
        self.half(0xbf011670, 173)  # distinct from stock refresh value 600
        self.put(0xbf001488, b'H_P_SSID=synthetic-session\0')
        self.put(0xbf018df4, bytes([192,0,2,20]))

    def session(self):
        return [self.load(a,n) for a,n in SESSION]

    def parse(self, path='/stats.json', method='GET', ip=21, cookie=None):
        self.output.clear(); self.entered.clear(); self.auth_entries.clear()
        raw = f'{method} {path} HTTP/1.1\r\nHost: 192.0.2.10\r\nContent-Length: 0\r\nContent-Type: application/x-www-form-urlencoded\r\n'
        if cookie is not None:
            raw += f'Cookie: H_P_SSID={cookie}\r\n'
        raw = (raw+'\r\n').encode()
        self.u.mem_protect(0x01000000, 0x10000, UC_PROT_ALL)
        self.put(http.REQUEST, bytes(0x2b0))
        self.put(http.PATH, raw+b'\0')
        self.put(http.REQUEST+0x298, bytes([192,0,2,ip]))
        self.u.reg_write(UC_MIPS_REG_A2,len(raw))
        result = self.run(function='stock_parser', preserve_request=True)
        self.u.mem_protect(0x01000000, 0x10000, UC_PROT_READ | UC_PROT_EXEC)
        return result

    def outer(self):
        return self.run(function='stock_outer', preserve_request=True)

class AnonymousHttpTests(unittest.TestCase):
    def assert_json(self, m):
        d=m.document()
        self.assertEqual(d['schema_version'],1)
        self.assertEqual(len(d['ports']),18)
        headers=bytes(m.output).split(b'\r\n\r\n',1)[0]
        self.assertIn(b'X-SwitchLens-Build: v0.1.6',headers)
        self.assertNotIn(b'set-cookie:',headers.lower())
        self.assertFalse(m.auth_entries)
        return d

    def test_anonymous_no_session_through_raw_parser_and_outer_gate(self):
        m=RawMachine();m.set_session(0);before=m.session()
        self.assertEqual(m.parse(),0);self.assertEqual(m.outer(),0)
        self.assert_json(m);self.assertEqual(m.session(),before)

    def test_any_cookie_and_same_or_other_ip_leave_entire_session_unchanged(self):
        for active in (0,1):
            for ip in (20,21):
                for cookie in (None,'wrong','synthetic-session'):
                    with self.subTest(active=active,ip=ip,cookie=cookie):
                        m=RawMachine();m.set_session(active);before=m.session()
                        self.assertEqual(m.parse(ip=ip,cookie=cookie),0)
                        self.assertEqual(m.outer(),0);self.assert_json(m)
                        self.assertEqual(m.session(),before)

    def test_admin_and_collector_interleaving(self):
        m=RawMachine()
        # The stock statistics renderer is stubbed; both auth gates execute.
        for _ in range(4):
            before=m.session()
            self.assertEqual(m.parse(),0);self.assertEqual(m.outer(),0)
            self.assert_json(m);self.assertEqual(m.session(),before)
            self.assertEqual(m.parse('/PortStatisticsRpm.htm',ip=20,cookie='synthetic-session'),0)
            # Stock authorized panel requests legitimately refresh TTL.
            m.outer_request=True
            m.outer()
            self.assertEqual(m.entered,[0xbfc4163c])
            self.assertEqual(m.load(0xbf011670,2),b'\x02\x58')
            self.assertEqual(m.session()[:2]+m.session()[3:],before[:2]+before[3:])
            m.outer_request=False

    def test_admin_get_and_post_keep_stock_authentication(self):
        for active in (0,1):
            for path in ADMIN:
                for method in ('GET','POST'):
                    with self.subTest(active=active,path=path,method=method):
                        m=RawMachine();m.set_session(active);before=m.session()
                        self.assertEqual(m.parse(path,method),0)
                        m.outer()
                        self.assertEqual(m.entered,[0xbfc3fc18])
                        self.assertFalse(m.output)
                        self.assertEqual(m.session(),before)
                        self.assertEqual(m.auth_entries,[0xbfc3ce50,0xbfc3b740])

    def test_near_paths_and_query_do_not_receive_exception(self):
        for path in ['/stats.jsonx','/stats.json/','/Stats.json','/stats.json?x=1',
                     '/stats.json?','/stats.json#x','//stats.json','/%73tats.json',
                     '/stats%2ejson','/stats.json%00','/stats.json;foo',
                     '/x/../stats.json','/stats.json/../reboot.cgi']:
            with self.subTest(path=path):
                m=RawMachine();before=m.session()
                self.assertEqual(m.parse(path),0);m.outer()
                self.assertEqual(m.entered,[0xbfc3fc18])
                self.assertEqual(m.session(),before)

    def test_methods_and_stock_get_prefix_quirk(self):
        for method in ['POST','HEAD','PUT','PATCH','DELETE','OPTIONS','get','GETX','GETTING']:
            with self.subTest(method=method):
                m=RawMachine();before=m.session()
                parsed=m.parse(method=method)
                if parsed==0:
                    m.outer()
                    self.assertEqual(m.entered,[0xbfc3fc18])
                else:
                    self.assertNotEqual(parsed,0)  # stock parser rejected it
                self.assertEqual(m.session(),before)
                self.assertNotIn(m.symbols['sg_http_entry'],m.entered)

    def test_inconsistent_parser_fields_fail_closed(self):
        for field in ('raw','target','path','method'):
            with self.subTest(field=field):
                m=RawMachine();self.assertEqual(m.parse(),0)
                if field=='raw':m.word(http.REQUEST+0x88,0)
                if field=='target':m.word(http.REQUEST+0x8c,http.PATH+5)
                if field=='path':m.put(http.REQUEST+8,b'/reboot.cgi\0')
                if field=='method':m.word(http.REQUEST+4,2)
                before=m.session();m.outer()
                self.assertEqual(m.entered,[0xbfc3fc18]);self.assertEqual(m.session(),before)

    def test_send_failure_does_not_fall_back_to_login_or_touch_session(self):
        m=RawMachine();before=m.session();m.send_fail=1
        self.assertEqual(m.parse(),0);self.assertNotEqual(m.outer(),0)
        self.assertFalse(m.auth_entries);self.assertEqual(m.session(),before)
        self.assertNotIn(0xbfc3fc18,m.entered)

    def test_legacy_v015_reproduces_early_denial(self):
        # Regression control uses the exact archived image, not our predicate.
        legacy=(ROOT/'releases/v0.1.5/SwitchLens-SG1218MPE-V5-v0.1.5.bin').read_bytes()
        self.assertEqual(hashlib.sha256(legacy).hexdigest(),'b2617a639869cf5ca0ef7b953b321f0625f3a1af3c6aab8d1a37a7ffa3dd6a7d')
        m=RawMachine();self.assertEqual(m.parse(),0)
        m.put(0xbfc08000,legacy);m.outer()
        self.assertEqual(m.entered,[0xbfc3fc18]);self.assertFalse(m.output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    args=p.parse_args()
    IMAGE=(args.build/'SwitchLens-SG1218MPE-V5-experimental.bin').read_bytes()
    MANIFEST=json.loads((args.build/'manifest.json').read_text())
    assert MANIFEST['anonymous_stats'] and MANIFEST['vendor_udp_management_disabled']
    http.SCHEMA=json.loads((ROOT/'schema/stats.schema.json').read_text())
    run=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AnonymousHttpTests))
    report=dict(tests=run.testsRun,failures=len(run.failures),errors=len(run.errors),
                image_sha256=hashlib.sha256(IMAGE).hexdigest(),
                scope='Stock raw MIPS HTTP parser and outer/inner authentication; synthetic sockets/MMIO; interleaving, not physical concurrency',
                hardware_verified=False)
    (args.build/'anonymous-http-test-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));sys.exit(not run.wasSuccessful())
