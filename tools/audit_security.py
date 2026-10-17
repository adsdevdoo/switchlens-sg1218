#!/usr/bin/env python3
"""Bounded stock security audit with synthetic inputs. No network/device I/O.

Factory persistence and socket transmission are stubbed. Results describe
callback behavior in specified RAM states, not live network exploitability.
"""
import hashlib
import json
from pathlib import Path
import re

from audit_cooling_paths import EXPECTED, call, get, machine, put, stub

ROOT = Path(__file__).resolve().parents[1]


def rc4(key, data):
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) % 256
        state[i], state[j] = state[j], state[i]
    i = j = 0
    result = bytearray()
    for value in data:
        i = (i + 1) % 256
        j = (j + state[i]) % 256
        state[i], state[j] = state[j], state[i]
        result.append(value ^ state[(state[i] + state[j]) % 256])
    return bytes(result)


def analyze(data):
    assert hashlib.sha256(data).hexdigest() == EXPECTED
    key = data[0xcb2e8:0xcb3e8]
    c = machine(data)
    addresses = (0xbf018000, 0xbf018040)
    fixtures = (b'audit-user'.ljust(16, b'\0'), b'synthetic-pass'.ljust(16, b'\0'))
    for addr, fixture in zip(addresses, fixtures):
        c.uc.mem_write(addr & 0x1fffffff, fixture)
    call(c, 0xbfc47c38, *addresses)
    for addr, fixture in zip(addresses, fixtures):
        assert bytes(c.uc.mem_read(addr & 0x1fffffff, 16)) == rc4(key, fixture)
    call(c, 0xbfc47c38, *addresses)
    for addr, fixture in zip(addresses, fixtures):
        assert bytes(c.uc.mem_read(addr & 0x1fffffff, 16)) == fixture

    cases = []
    # No handshake or live packets: directly test the existing callback in
    # explicitly selected states, with zeroed HTTP session and synthetic data.
    for state in (0, 1, 2, 3):
        for opcode, length, offset in ((6, 6, 0), (14, 40, 0x96), (11, 128, 6)):
            c, writes = machine(data), []
            put(c, 0xbf0015c0, state)
            put(c, 0xbf011660, 0)
            stub(c, 0xbf01ca4c)
            stub(c, 0xbfc52edc, lambda a: writes.append(a[1:3]))
            def unexpected_credentials(a):
                raise AssertionError('Credential getter unexpectedly invoked')
            stub(c, 0xbfc543a4, unexpected_credentials)
            packet = bytearray(12 + length)
            packet[1] = opcode
            c.uc.mem_write(0x1f018000, bytes(packet))
            call(c, 0xbfc4e238, 0, 0xbf018000, len(packet), 0)
            assert writes == ([[offset, length]] if state < 2 else [])
            cases.append(dict(initial_state=state, opcode=opcode,
                              factory_write_calls=writes, http_session_active=False))

    routes = sorted(set(m.group().decode() for m in
                        re.finditer(rb'/[A-Za-z0-9_./-]+\.(?:cgi|htm|html)(?=\x00)', data)))
    return dict(stock_sha256=EXPECTED,
                method='Bounded static review and synthetic MIPS execution; no live device traffic',
                fixed_key=dict(file_offset='0xcb2e8', bytes=256,
                               sha256=hashlib.sha256(key).hexdigest(),
                               credential_codec_matches_rc4=True, round_trip=True),
                tddp_initial_state=get(machine(data), 0xbf0015c0),
                tddp_callback_cases=cases,
                tddp_limit='State 2 is the initialized value. Tests force states 0..3; live state transitions and network reachability are not proven.',
                literal_http_routes=routes,
                route_limit='String inventory only; not proof of exhaustive handlers or authorization',
                factory_write_helper='0xbfc52edc: reads 0xb41fc000..0xb41fc0c2, updates selected bytes, erases sector 0x1fc and writes 0xc2 bytes',
                conclusions_not_established=['Intentional backdoor', 'Universal absence of hidden accounts', 'Live unauthenticated factory write', 'Complete firmware security'])


if __name__ == '__main__':
    data = (ROOT/'vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin').read_bytes()
    print(json.dumps(analyze(data), indent=2))
