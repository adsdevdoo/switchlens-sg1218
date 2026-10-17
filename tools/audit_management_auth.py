#!/usr/bin/env python3
"""Offline MIPS authentication follow-up. No sockets or device/flash writes.

Runs pinned release bytes. Network primitives and factory persistence are
replaced by recording stubs. TSDP runs stop at explicit authorization checkpoints.
This is callback-level evidence, not a complete boot/network-stack simulation.
"""
import hashlib
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.mips_const import (UC_MIPS_REG_PC, UC_MIPS_REG_RA,
                               UC_MIPS_REG_SP, UC_MIPS_REG_V0, UC_MIPS_REG_S1)
from audit_cooling_paths import ARGS, call, get, machine, put, stub
from audit_security import rc4
from test_uart_console import RETURN, STACK

ROOT = Path(__file__).resolve().parents[1]
IMAGES = {
    'stock': ('vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin',
              'c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32'),
    'v0.1.4': ('releases/v0.1.4/SwitchLens-SG1218MPE-V5-v0.1.4.bin',
               '4093f2e0dfcbbbc1c0caf0ed1d9d8902de747aa41e9525840b4755004e791b93'),
    'v0.1.5': ('releases/v0.1.5/SwitchLens-SG1218MPE-V5-v0.1.5.bin',
               'b2617a639869cf5ca0ef7b953b321f0625f3a1af3c6aab8d1a37a7ffa3dd6a7d'),
}


def reject_call(args):
    raise AssertionError('Unexpected credential or persistence call')


def boot_bss(data):
    c = machine(data)
    put(c, 0xbf013690, 0xdeadbeef)
    c.uc.emu_start(0xbfc08684, 0xbfc086a4, count=2000000)
    assert c.uc.reg_read(UC_MIPS_REG_PC) == 0xbfc086a4
    assert get(c, 0xbf013690) == 0
    assert get(c, 0xbf0015c0) == 2
    return dict(start='0xbfc08684', end_exclusive='0xbfc086a4',
                counter_after=0, initialized_state_preserved=2)


def tddp(data, disabled):
    results = []
    for opcode, length, offset in ((6, 6, 0), (14, 40, 0x96), (11, 128, 6)):
        c, writes, replies = machine(data), [], []
        # Preserve the image's initialized state; do not force states 0/1.
        assert get(c, 0xbf0015c0) == 2
        assert get(c, 0xbf013690) == 0  # Synthetic zero-filled BSS.
        assert get(c, 0xbf011660) == 0  # No synthetic HTTP session.
        stub(c, 0xbfc543a4, reject_call)
        stub(c, 0xbfc52edc, lambda a: writes.append(a[1:3]))
        stub(c, 0xbf01ca4c, lambda a: replies.append(
            bytes(c.uc.mem_read(a[1] & 0x1fffffff, a[2])).hex()))
        def receive(packet):
            c.uc.mem_write(0x1f018000, bytes(packet))
            call(c, 0xbfc4e238, 0, 0xbf018000, len(packet), 0)
        packet = bytearray(12 + length)
        packet[0:3] = bytes((1, opcode, 1))
        receive(packet)
        assert not writes and not replies and get(c, 0xbf0015c0) == 2
        handshake = bytearray(12)
        handshake[0:3] = bytes((1, 12, 1))
        receive(handshake)
        after = get(c, 0xbf0015c0)
        assert after == (2 if disabled else 0)
        receive(packet)
        assert writes == ([] if disabled else [[offset, length]])
        results.append(dict(opcode=opcode, initial_state=2,
                            direct_request_rejected=True, state_after_handshake=after,
                            factory_helper_calls=writes, response_count=len(replies),
                            credential_getter_calls=0))
    return results


def tddp_controls(data):
    results = []
    for name, packet_type, send_result in [('wrong_type', 0, 0), ('send_failure', 1, 0xffffffff)]:
        c = machine(data)
        stub(c, 0xbfc543a4, reject_call)
        stub(c, 0xbfc52edc, reject_call)
        def send(uc, address, size, unused):
            uc.reg_write(UC_MIPS_REG_V0, send_result)
            uc.reg_write(UC_MIPS_REG_PC, uc.reg_read(UC_MIPS_REG_RA))
        c.uc.hook_add(UC_HOOK_CODE, send, begin=0xbf01ca4c, end=0xbf01ca4c)
        packet = bytearray(12)
        packet[:3] = bytes((1, 12, packet_type))
        c.uc.mem_write(0x1f018000, bytes(packet))
        call(c, 0xbfc4e238, 0, 0xbf018000, len(packet), 0)
        assert get(c, 0xbf0015c0) == 2
        results.append(dict(case=name, final_state=2))
    return results


def tsdp(data, disabled):
    results = []
    fixtures = [('missing_credentials', 3, b'', b'', True),
                ('wrong_password', 3, b'audit-user', b'incorrect', True),
                ('correct_credentials', 3, b'audit-user', b'synthetic-pass', True),
                ('wrong_session_token', 3, b'audit-user', b'synthetic-pass', False),
                ('read_password_tlv', 1, b'', b'', True)]
    for name, kind, username, password, valid_token in fixtures:
        c, events = machine(data), []
        stub(c, 0xbfc38780)  # Successful socket creation; no host sockets.
        stub(c, 0xbfc38b3c)  # Successful bind.
        call(c, 0xbfc47cf0)
        mac = bytes.fromhex('020000000001')
        stub(c, 0xbfc51378, lambda a: c.uc.mem_write(a[0] & 0x1fffffff, mac))
        def credentials(a):
            events.append('configured_credentials_read')
            c.uc.mem_write(a[0] & 0x1fffffff, b'audit-user'.ljust(17, b'\0'))
            c.uc.mem_write(a[1] & 0x1fffffff, b'synthetic-pass'.ljust(17, b'\0'))
        stub(c, 0xbfc543a4, credentials)
        for address in (0xbfc52edc, 0xbfc54470, 0xbfc541dc, 0xbf01ca4c):
            stub(c, address, reject_call)
        token = 0x1234
        c.uc.mem_write(0x1f0116d0, struct.pack('>H', token))
        def tlv(code, payload=b''):
            return struct.pack('>HH', code, len(payload)) + payload
        payload = tlv(0xffff)
        if kind == 1:
            payload = tlv(0x0202) + payload
        elif username:
            payload = tlv(0x0200, username) + tlv(0x0202, password) + payload
        packet = bytearray(32) + payload
        packet[0:2] = bytes((1, kind))
        packet[2:8] = mac
        struct.pack_into('>H', packet, 20, len(packet))
        struct.pack_into('>H', packet, 26, token if valid_token else token + 1)
        c.uc.mem_write(0x1f018000, rc4(data[0xcb2e8:0xcb3e8], packet))
        checkpoints = {0xbfc49124: 'credentials_accepted',
                       0xbfc4a728: 'request_rejected',
                       0xbfc4a72c: 'request_rejected',
                       0xbfc4a738: 'preauth_request_accepted'}
        def checkpoint(uc, address, size, unused):
            events.append(checkpoints[address])
            uc.emu_stop()
        for address in checkpoints:
            c.uc.hook_add(UC_HOOK_CODE, checkpoint, begin=address, end=address)
        c.uc.reg_write(UC_MIPS_REG_SP, STACK)
        c.uc.reg_write(UC_MIPS_REG_RA, RETURN)
        for register, value in zip(ARGS, (0, 0xbf018000, len(packet), 0)):
            c.uc.reg_write(register, value)
        c.uc.emu_start(0xbfc48db0, RETURN, count=2000000)
        pc = c.uc.reg_read(UC_MIPS_REG_PC)
        assert pc in checkpoints or pc == RETURN, hex(pc)
        expected = [] if disabled or not valid_token else (
            ['configured_credentials_read', 'credentials_accepted'] if name == 'correct_credentials'
            else ['configured_credentials_read', 'request_rejected'] if name == 'wrong_password'
            else ['request_rejected'])
        assert events == expected, (name, events, expected)
        results.append(dict(case=name, events=events, stopped_at=hex(pc),
                            error_code=(c.uc.reg_read(UC_MIPS_REG_S1)
                                        if events and events[-1] == 'request_rejected' else None)))
    return results


def analyze():
    results = {}
    for name, (path, expected) in IMAGES.items():
        data = (ROOT / path).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        results[name] = dict(sha256=expected, boot_bss=boot_bss(data),
                             tddp=tddp(data, name == 'v0.1.5'),
                             tddp_controls=tddp_controls(data),
                             tsdp=tsdp(data, name == 'v0.1.5'))
    return dict(method='Original MIPS instructions, synthetic callback inputs; no network I/O',
                limits=['Boot BSS-clear loop checked separately; no complete hardware boot',
                        'TDDP send returns success; factory persistence records arguments only',
                        'TSDP configured credentials and MAC are synthetic; execution stops at authorization checkpoints',
                        'No live reachability, flash-write or complete parser-safety claim'],
                images=results)


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2))
