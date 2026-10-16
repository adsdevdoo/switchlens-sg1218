#!/usr/bin/env python3
"""Host tests. All values are synthetic; no switch access."""
import json
import pathlib
import re
import subprocess
import sys
import unittest
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXE = str(pathlib.Path(sys.argv.pop(1)).resolve())
SCHEMA = json.loads((ROOT / 'schema/stats.schema.json').read_text())
VALIDATOR = Draft202012Validator(SCHEMA)

def run(**kw):
    args = [EXE]
    for key, value in kw.items():
        args += ['--' + key.replace('_', '-'), str(value)]
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    # Sanitizer failures cannot be mistaken for expected fixture errors.
    meta = json.loads(p.stderr)
    assert p.returncode == (0 if meta['status'] == 0 else 1), p.stderr
    assert meta['bytes'] == len(p.stdout)
    assert meta['forced_gets'] == 0
    return p.stdout, meta

def valid(**kw):
    data, meta = run(**kw)
    assert meta['status'] == 0, meta
    doc = json.loads(data)
    VALIDATOR.validate(doc)
    return doc, meta

class Serializer(unittest.TestCase):
    def test_complete_schema_and_system_poe(self):
        doc, meta = valid()
        self.assertEqual([p['port'] for p in doc['ports']], list(range(1,19)))
        self.assertEqual(doc['system']['name'], doc['system']['description'])
        self.assertEqual(doc['system']['description'], 'Lab "A"\\\nпорт')
        self.assertEqual(doc['poe']['consumption_w'], 12.3)
        self.assertEqual(doc['ports'][0]['poe']['voltage_v'], 50)
        self.assertTrue(all(p['poe'] is not None for p in doc['ports'][:16]))
        self.assertTrue(all(p['poe'] is None for p in doc['ports'][16:]))
        self.assertEqual(meta['finishes'], 1)
        self.assertEqual(meta['invalid'], 0)
        self.assertEqual(meta['unavailable'], 0)

    def test_u64_exact_and_unknown_counters(self):
        for value in (0, 2**32-1, 2**32, 2**53+1, 2**64-1):
            with self.subTest(value=value):
                doc, _ = valid(counter=value)
                for port in doc['ports']:
                    self.assertEqual(port['counters']['rx_bytes'], str(value))
                    self.assertEqual(port['counters']['tx_bytes'], str(value))
                    self.assertIsNone(port['counters']['rx_discards'])
                    self.assertIsNone(port['counters']['tx_packets_256_511'])

    def test_partial_write_preserves_bytes(self):
        original, _ = run()
        for chunk in (1, 7, 127, 128):
            with self.subTest(chunk=chunk):
                data, meta = run(chunk=chunk)
                self.assertEqual(data, original)
                self.assertEqual(meta['status'], 0)

    def test_transport_error_and_zero_progress(self):
        original, _ = run()
        for mode in (0, 4):
            for stop in (0, 1, 127, 128, 129, len(original)-1):
                with self.subTest(mode=mode, stop=stop):
                    data, meta = run(mode=mode, stop=stop)
                    self.assertEqual(data, original[:stop])
                    self.assertEqual(meta['status'], -1)
                    self.assertEqual(meta['finishes'], 0)
                    # One final error callback; no infinite no-progress retry.
                    self.assertLessEqual(meta['writes'], stop//128+2)

    def test_finish_failure(self):
        data, meta = run(finish_fail=1)
        self.assertEqual(meta['status'], -1)
        self.assertEqual(meta['finishes'], 1)
        self.assertTrue(data.endswith(b'}}'))

    def test_unknown_unavailable_and_invalid(self):
        for mode in (1, 2, 3):
            with self.subTest(mode=mode):
                doc, meta = valid(mode=mode)
                self.assertIsNone(doc['system']['description'])
                self.assertIsNone(doc['ports'][0]['counters']['rx_bytes'])
                self.assertEqual(meta['unavailable'], meta['gets'] if mode==2 else 0)
                self.assertEqual(meta['invalid'], meta['gets'] if mode==3 else 0)

    def test_source_failure(self):
        for scope in range(4):
            data, meta = run(fail_scope=scope)
            self.assertEqual(meta['status'], -2)
            self.assertEqual(meta['finishes'], 0)
        _, meta = run(unknown_poe=1)
        self.assertEqual(meta['status'], -2)

    def test_utf8_escaping_and_bounds(self):
        for text in ('', 'a'*32, 'я'*16, '\x00\b\t\n\r\x1f"\\', '😀\u2028'):
            with self.subTest(text=repr(text)):
                doc, meta = valid(text_hex=text.encode().hex())
                self.assertEqual(doc['system']['description'], text)
                self.assertEqual(meta['invalid'], 0)
        for raw in (b'a'*33, b'\xc0\x80', b'\xe0\x80\x80', b'\xed\xa0\x80',
                    b'\xf0\x80\x80\x80', b'\xf4\x90\x80\x80', b'\xf5\x80\x80\x80',
                    b'\xe2\x82', b'\x80', b'\xc2A'):
            with self.subTest(raw=raw.hex()):
                doc, meta = valid(text_hex=raw.hex())
                self.assertIsNone(doc['system']['description'])
                self.assertIsNone(doc['system']['name'])
                self.assertEqual(meta['invalid'], 2)

    def test_reader_offsets_against_static_evidence(self):
        evidence = json.loads((ROOT/'research/mib-map.json').read_text())
        selectors = {x['selector']:x for x in evidence['selectors']}
        source = (ROOT/'src/sg_mib.c').read_text()
        table = source.split('map[]={',1)[1].split('};',1)[0]
        entries = re.findall(r'\{(\d+),(0x[0-9a-f]+)\}', table)
        self.assertEqual(len(entries), 41)
        for selector, offset in entries:
            item = selectors[int(selector)]
            self.assertEqual(item['register_offsets'], [hex(int(offset,16))])
            self.assertEqual(item['classification'], 'single_word_counter')
        self.assertNotIn('58', [s for s, _ in entries])
        for selector, expected in ((1, ['0x4','0x0']), (9,['0xc','0x8'])):
            self.assertEqual(selectors[selector]['register_offsets'], expected)
            self.assertEqual(selectors[selector]['classification'], 'two_word_counter')

if __name__ == '__main__':
    unittest.main(verbosity=2)
