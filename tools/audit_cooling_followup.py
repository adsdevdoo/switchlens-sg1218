#!/usr/bin/env python3
"""Offline boot/timer/cross-version cooling investigation. No device access."""
import hashlib
import json
from pathlib import Path
import re
import struct
from types import SimpleNamespace

from unicorn import (Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_BIG_ENDIAN,
                     UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE)
from unicorn.mips_const import UC_CPU_MIPS32_24KF
from audit_cooling_paths import EXPECTED, call, direct_refs, get, machine, put, stub
from audit_gpio_inventory import pairs

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/tp-link/tl-sg1218mpe-v5'
HASHES = {
    '20220921': '4621d6e9742539c5b95c76d203dcd21d93b2a35150967a415ef8e83f84cdb2bb',
    '20221012': '4b5f2348480fcb8a908a2ef7a76d1a4d82e754375cece9a24a3e3038120d9cf3',
    '20230220': '0bcbe30cb88a0987967cb1b30eac01060a48eec2cbdcbd94091ea6e0dfd3a6b9',
    '20230616': EXPECTED,
}
DUMP_HASH = 'b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87'


def word(data, off):
    return struct.unpack_from('>I', data, off)[0]


def address(data, upper, lower):
    low = word(data, lower) & 0xffff
    return (((word(data, upper) & 0xffff) << 16) +
            (low if low < 0x8000 else low - 0x10000)) & 0xffffffff


def bare(data, flash_start=0x1fc08000):
    uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(UC_CPU_MIPS32_24KF)
    uc.mem_map(0x1fc00000, 0x200000)
    uc.mem_map(0x1f000000, 0x20000)
    uc.mem_map(0x18003000, 0x1000)
    uc.mem_write(flash_start, data)
    return SimpleNamespace(uc=uc)


def version_policy(data):
    found = [i for i in range(0, len(data)-3, 4) if word(data, i) == 0x28a205dd]
    assert len(found) == 1
    start = found[0] - 0x84
    assert word(data, start) == 0x2c820002
    assert word(data, start + 0x10) == 0x2404001b  # GPIO27
    assert word(data, start + 0x98) == 0x28a205b4
    state = address(data, start + 0x64, start + 0x68)
    cache = address(data, start + 0x24, start + 0x28)
    power_sum = address(data, start + 0x6c, start + 0x74)
    writer = 0xb0000000 | ((word(data, start + 0x14) & 0x3ffffff) << 2)
    c = bare(data)
    writes = []
    stub(c, writer, lambda a: writes.append(a[:2]))
    put(c, cache + 4, 1)
    put(c, cache + 8, 16)
    cases = []
    samples = [(s, p) for s in (0, 1) for p in (-1, 0, 1459, 1460, 1500, 1501, 1600, 32767)]
    samples += [(s, p) for s in (2, 0xffffffff) for p in (0, 1600)]
    for previous, load in samples:
        writes.clear()
        put(c, state, previous)
        c.uc.mem_write((cache + 48 + 10) & 0x1fffffff, struct.pack('>h', load))
        call(c, 0xbfc08000 + start + 0x24)
        expected = (1 if previous == 0 and load < 1460 else
                    0 if previous == 1 and load >= 1501 else previous)
        assert get(c, state) == expected
        assert get(c, power_sum) == load & 0xffffffff
        assert writes == ([[27, expected]] if expected in (0, 1) else [])
        cases.append({'previous_state': previous, 'load': load, 'new_state': expected,
                      'gpio_calls': [list(v) for v in writes]})
    return {'wrapper_file_offset': hex(start), 'policy_file_offset': hex(start + 0x24),
            'policy_sha256': hashlib.sha256(data[start:start + 0xb8]).hexdigest(),
            'cache_address': hex(cache), 'state_address': hex(state),
            'sum_address': hex(power_sum), 'mocked_gpio_writer': hex(writer),
            'cases_passed': len(cases), 'cases': cases}


def boot_setup(dump):
    boot = dump[:0x8000]
    cases = []
    for initial in (0, 0xffffffff, 0xa5a55a5a):
        c = bare(boot, 0x1fc00000)
        c.uc.mem_map(0x1b000000, 0x10000)
        for addr in (0xb8003500, 0xb8003508, 0xb800350c):
            put(c, addr, initial)
        accesses = []
        c.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE,
                      lambda uc, kind, addr, size, val, unused:
                      accesses.append([kind, hex(addr), hex(val)]),
                      begin=0x18003500, end=0x1800353f)
        trace = []
        c.uc.hook_add(UC_HOOK_CODE, lambda uc, pc, size, unused: trace.append(pc))
        # Only the exact GPIO setup slice; no flash write/recovery execution.
        c.uc.emu_start(0xbfc05c98, 0xbfc05cf4, count=100)
        assert trace == list(range(0xbfc05c98, 0xbfc05cf4, 4))
        assert get(c, 0xb8003500) == initial & ~(1 << 24)
        assert get(c, 0xb8003508) == initial | (1 << 24)
        assert get(c, 0xb800350c) == initial | (1 << 24)
        cases.append({'initial': hex(initial), 'accesses': accesses,
                      'gpio27_preserved': True})
    # Literal base constructors across the boot prefix, including data. Each
    # is a candidate requiring manual review, not a complete address analysis.
    bases = []
    for off in range(0, len(boot)-3, 4):
        w = word(boot, off)
        if w >> 26 == 15 and w & 0xffff in (0xb800, 0x9800, 0x1800, 0x0b80):
            bases.append(hex(off))
    return {'dump_sha256': DUMP_HASH, 'boot_prefix_bytes': len(boot),
            'boot_prefix_sha256': hashlib.sha256(boot).hexdigest(),
            'reviewed_slice': ['0x5c98', '0x5cf4'], 'cases': cases,
            'base_constructor_candidates': bases,
            'scope': 'GPIO setup slice and static base-constructor review, not full boot emulation'}


def timer(data):
    c = machine(data)
    accesses = []
    c.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE,
                  lambda uc, kind, addr, size, value, unused:
                  accesses.append([kind, hex(addr), hex(value)]),
                  begin=0x18003000, end=0x18003fff)
    call(c, 0xbfc104b0, 0)
    call(c, 0xbfc10504, 0)
    initialization = list(accesses)
    accesses.clear()
    for _ in range(100):
        call(c, 0xbf01a094)
    assert get(c, 0xbf002e94) == 100
    assert get(c, 0xbf002e90) == 5
    assert {row[1] for row in accesses} == {'0x1800310c'}
    return {'init_entry': '0xbfc104b0', 'start_entry': '0xbfc10504',
            'isr_entry': '0xbf01a094', 'mocked_calls': [],
            'initialization_accesses': initialization, 'irq_calls': 100,
            'fast_counter_after': 100, 'uptime_counter_after': 5,
            'isr_mmio_addresses': sorted({row[1] for row in accesses}),
            'gpio_accesses': 0,
            'seconds_per_irq': None,
            'note': 'Software counters and synthetic MMIO; hardware timer does not run in this test'}


def main():
    versions, data = {}, None
    for date, expected in HASHES.items():
        path = next((VENDOR / date).glob('*.bin'))
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        versions[date] = {'sha256': expected, **version_policy(data)}
    dump = (ROOT / 'backups/original/2026-10-17/GD25Q16B-xgpro-original.bin').read_bytes()
    assert hashlib.sha256(dump).hexdigest() == DUMP_HASH
    targets = [0xbfc104b0, 0xbfc10504, 0xbf01a094, 0xbfc107ec,
               0xbfc10810, 0xbfc10824, 0xbfc10848, 0xbfc11614, 0xbfc11590]
    constructed = pairs(data, targets)
    refs = {hex(t): {'direct_offsets': direct_refs(data, t),
                    'constructed_candidates': constructed[t],
                    'aligned_literals': [hex(i) for i in range(0, len(data)-3, 4)
                                         if word(data, i) == t]} for t in targets}
    names = {}
    pattern = re.compile(rb'(?:^|[_\s])(?:fan|fans|thermal|pwm|tach|temperature|cooling)(?:[_\s]|$)', re.I)
    for label, blob in [('runtime_20230616', data), ('boot_prefix', dump[:0x8000])]:
        names[label] = [{'offset': hex(m.start()), 'length': len(m.group()),
                         'prefix': m.group()[:200].decode()}
                        for m in re.finditer(rb'[\x20-\x7e]{4,}', blob) if pattern.search(m.group())]
    print(json.dumps({'device_access': False, 'versions': versions,
                      'total_policy_cases': sum(v['cases_passed'] for v in versions.values()),
                      'boot': boot_setup(dump), 'timer': timer(data),
                      'additional_references': refs, 'bounded_string_search': names,
                      'limits': ['No proof against all computed addresses/calls',
                                 'No physical fan circuit or RPM identified',
                                 'Counter ratio is not wall-clock calibration',
                                 'Cross-version result applies to the identified controller, not every routine']}, indent=2))


if __name__ == '__main__':
    main()
