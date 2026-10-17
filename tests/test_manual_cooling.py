#!/usr/bin/env python3
"""v0.1.5 persistent RAM cooling modes; synthetic MIPS execution, no device I/O."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest
import test_cooling as old
from test_cooling import machine, send, power, put, get, call, STATE, TICKS, DATA, BIT
import test_target as http
TAG = 0xd8000000

class ManualCooling(unittest.TestCase):
    def test_manual_survives_ticks_and_poe_changes(self):
        for command, level in [('fast', 0), ('low', 1)]:
            for initial in (0, 1):
                c = machine(state=initial)
                self.assertIn(b'no timeout', send(c, 'cool '+command))
                packed = TAG | initial << 25 | level << 24
                for tick in (1100, 0xffffff, 0xffffffff, 0):
                    for load in (0, 1459, 1460, 1500, 1501, 2500):
                        put(c, TICKS, tick)
                        power(c, load)
                        call(c, 0xbfc5c368)
                        c.dispatch()
                        self.assertEqual(get(c, STATE), packed)
                        self.assertEqual(get(c, DATA), (0x39780000 & ~BIT) | level << 27)

    def test_switch_modes_then_auto_uses_current_load_and_saved_hysteresis(self):
        for initial in (0, 1):
            for load in (0, 1460, 1500, 1501):
                c = machine(state=initial)
                for cmd, level in [('low', 1), ('fast', 0), ('low', 1)]:
                    send(c, 'cool '+cmd)
                    self.assertEqual(get(c, STATE), TAG | initial << 25 | level << 24)
                power(c, load)
                send(c, 'cool auto')
                expected = 1 if load < 1460 else 0 if load >= 1501 else initial
                self.assertEqual(get(c, STATE), expected)
                self.assertEqual((get(c, DATA)>>27)&1, expected)

    def test_help_and_status_are_read_only_and_old_test_command_removed(self):
        c = machine()
        self.assertIn(b'cool low', send(c, 'help cool'))
        self.assertIn(b'speed_mode=low', send(c, 'cool status'))
        for cmd in ['cool test 0', 'cool slow', 'cool fast extra', 'cool low extra', 'cool unknown']:
            send(c, cmd)
            self.assertEqual(get(c, STATE), 1)
            self.assertEqual(get(c, DATA), 0x39780000)
        send(c, 'cool fast')
        self.assertIn(b'mode=manual; no timeout', send(c, 'cool status'))
        self.assertIn(b'speed_mode=fast', send(c, 'cool status'))

    def test_guard_invalid_state_mux_direction_and_reg_write(self):
        for address, value in [(STATE, 2), (0xb8003500, BIT), (0xb8003508, 0)]:
            for command in ('low', 'fast'):
                c = machine()
                put(c, address, value)
                before = get(c, STATE)
                self.assertIn(b'unchanged', send(c, 'cool '+command))
                self.assertEqual(get(c, STATE), before)
        c = machine()
        send(c, 'cool fast')
        self.assertIn(b'writes blocked', send(c, 'reg socset 0x350c 0'))
        self.assertEqual(get(c, DATA), 0x31780000)

    def test_json_authenticated_read_only_manual_auto_invalid_and_mux(self):
        for state, level, mode in [(1, 1, 'auto'), (0, 0, 'auto'),
                (TAG | 1<<25, 0, 'manual'), (TAG | 1<<24, 1, 'manual'), (2, 0, 'invalid')]:
            for control, direction in [(0, BIT), (BIT, BIT), (0, 0)]:
                m = http.Machine(old.IMAGE, old.MANIFEST)
                m.word(0xbf011660, 1)
                m.put(0xbf001488, b'required-session\0')
                m.put(http.REQUEST+0xec, b'required-session\0')
                m.word(STATE, state)
                m.word(0xb8003500, control)
                m.word(0xb8003508, direction)
                m.word(DATA, level << 27)
                m.run()
                d = m.document()['cooling']
                expected = None if state==2 or control or not direction else 'low' if level else 'fast'
                self.assertEqual(d['speed_mode'], expected)
                self.assertEqual(d['mode'], mode)
                for key in ('test_level','remaining_ticks','test_limit_ticks','fan_rpm','fan_status'):
                    self.assertIsNone(d[key])
                self.assertEqual(m.load(STATE, 4), struct.pack('>I', state))

    def test_normal_state_runs_stock_policy(self):
        # Verify the policy from an ordinary 0/1 state; this is not a reboot test.
        c = machine(state=TAG | 1<<24)
        put(c, STATE, 0)  # normal startup state, not a simulated complete reboot
        power(c, 0)
        call(c, 0xbfc5c368)
        self.assertEqual(get(c, STATE), 1)
        self.assertEqual((get(c, DATA)>>27)&1, 1)

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    args=p.parse_args()
    old.IMAGE=(args.build/'SwitchLens-SG1218MPE-V5-experimental.bin').read_bytes()
    old.MANIFEST=json.loads((args.build/'manifest.json').read_text())
    http.SCHEMA=json.loads((old.ROOT/'schema/stats.schema.json').read_text())
    run=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ManualCooling))
    report=dict(tests=run.testsRun, failures=len(run.failures), errors=len(run.errors), image_sha256=hashlib.sha256(old.IMAGE).hexdigest(), scope='Synthetic MIPS CLI/controller/HTTP; no physical board test')
    (args.build/'manual-cooling-test-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    sys.exit(not run.wasSuccessful())
