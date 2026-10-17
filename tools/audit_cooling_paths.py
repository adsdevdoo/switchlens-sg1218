#!/usr/bin/env python3
"""Trace stock GPIO and PoE bus paths offline; never accesses a device.

Execute original MIPS code with synthetic GPIO/PoE inputs. Bus transfers,
delay and LED hardware calls are mocked explicitly. This does not identify
the physical fan circuit, the PSE chip model or unobserved execution paths.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_EXEC
from unicorn.mips_const import (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2,
                               UC_MIPS_REG_A3, UC_MIPS_REG_PC, UC_MIPS_REG_RA,
                               UC_MIPS_REG_SP, UC_MIPS_REG_V0)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_uart_console import Console, RETURN, STACK

EXPECTED = 'c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32'
ARGS = (UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3)
RANGES = ((0x10, 0x720), (0x3160, 0x8178), (0x8178, 0x91700))


def va(off):
    return off + (0xbf019528 - 0x3160 if 0x3160 <= off < 0x8178 else 0xbfc08000)


def direct_refs(data, target):
    result = []
    for start, end in RANGES:
        for off in range(start, end, 4):
            word, = struct.unpack_from('>I', data, off)
            if word >> 26 in (2, 3) and (((va(off) + 4) & 0xf0000000) |
                                       ((word & 0x3ffffff) << 2)) == target:
                result.append(hex(off))
    return result


def put(c, addr, value):
    c.uc.mem_write(addr & 0x1fffffff, struct.pack('>I', value))


def get(c, addr):
    return struct.unpack('>I', c.uc.mem_read(addr & 0x1fffffff, 4))[0]


def machine(data):
    c = Console(data)
    c.uc.mem_map(0x18003000, 0x1000)
    c.uc.mem_protect(0x1fc00000, 0x200000, UC_PROT_READ | UC_PROT_EXEC)
    return c


def call(c, address, *args):
    c.uc.reg_write(UC_MIPS_REG_SP, STACK)
    c.uc.reg_write(UC_MIPS_REG_RA, RETURN)
    for reg, value in zip(ARGS, args):
        c.uc.reg_write(reg, value)
    c.uc.emu_start(address, RETURN, count=2000000)
    if c.uc.reg_read(UC_MIPS_REG_PC) != RETURN or c.uc.reg_read(UC_MIPS_REG_SP) != STACK:
        raise AssertionError('Instruction budget exceeded or stack not restored')


def stub(c, address, action=None):
    def hook(uc, pc, size, unused):
        args = [uc.reg_read(r) for r in ARGS]
        if action:
            action(args)
        uc.reg_write(UC_MIPS_REG_V0, 0)
        uc.reg_write(UC_MIPS_REG_PC, uc.reg_read(UC_MIPS_REG_RA))
    c.uc.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)


def analyze(data):
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError('Unexpected image SHA-256')
    c = machine(data)
    writes, reads, gpio_writes = [], [], []
    stub(c, 0xbf01a1dc)  # Delay only; no wall-clock timing inferred.
    stub(c, 0xbfc101c0)  # Platform helper called by bus setup.
    stub(c, 0xbfc5c7a8, lambda a: writes.append(a[:3]))

    def read_bus(a):
        reads.append(a[:2])
        c.uc.mem_write(a[2] & 0x1fffffff, b'\0')

    stub(c, 0xbfc5ca08, read_bus)
    c.uc.hook_add(UC_HOOK_MEM_WRITE,
                  lambda uc, access, addr, size, value, user: gpio_writes.append(hex(value)),
                  begin=0x1800350c, end=0x1800350f)
    call(c, 0xbfc5e994)
    init_table = [list(pair) for pair in zip(data[0xcb65c:0xcb66a:2], data[0xcb65d:0xcb66a:2])]
    expected = []
    for device in (0x20, 0x21, 0x22, 0x23):
        expected.extend([device, reg, value] for reg, value in init_table)
        for port in range(4):
            expected.extend(([device, 0x13 + port, 4], [device, 0x17 + port, 1]))
    assert writes == expected
    assert reads == [[device, 0x21] for device in (0x20, 0x21, 0x22, 0x23)]
    assert get(c, 0xb8003508) & 0x3d000000 == 0x39000000
    assert get(c, 0xb800350c) & (1 << 27) == 0

    # Combined stock poll, not just isolated controller: GPIO26 and LED enable
    # can change independently while the same PoE sum selects the same GPIO27.
    cases = []
    for enabled in (0, 1):
        for level in (0, 1):
            for state in (0, 1):
                for power in (0, 1460, 1500, 1501):
                    m = machine(data)
                    led_calls = []
                    stub(m, 0xbfc26828)
                    stub(m, 0xbfc26830, lambda a: led_calls.append(a))
                    put(m, 0xbf0023d0, enabled)
                    put(m, 0xbf0143e4, 1)
                    put(m, 0xbf0143e8, 16)
                    put(m, 0xbf0143f4, 2500)
                    put(m, 0xbf014840, state)
                    put(m, 0xb800350c, level << 26)
                    m.uc.mem_write(0x1f0143e0 + 48 + 10, struct.pack('>h', power))
                    call(m, 0xbfc5e2fc)
                    expected_level = 1 if power < 1460 else 0 if power >= 1501 else state
                    actual = get(m, 0xb800350c) >> 27 & 1
                    assert actual == expected_level
                    assert get(m, 0xbf014840) == expected_level
                    modes = [a[3] for a in led_calls if a[1] in (26, 27) and a[2] == 0]
                    assert modes == [5 if enabled and level else 0,
                                     5 if enabled and not level else 0]
                    cases.append({'led_enable': enabled, 'gpio26': level,
                                  'previous_state': state, 'power_raw': power,
                                  'gpio27_after': actual, 'led_modes_26_27': modes})

    targets = (0xbf0196b4, 0xbf0196f0, 0xbf01978c, 0xbf019864,
               0xbfc5c344, 0xbfc5c49c, 0xbfc5c7a8, 0xbfc5c874,
               0xbfc5c904, 0xbfc5ca08, 0xbfc5cb2c, 0xbfc5cbd8, 0xbfc5d0f8)
    refs = {}
    for target in targets:
        packed = struct.pack('>I', target)
        refs[hex(target)] = {
            'direct_j_jal_file_offsets': direct_refs(data, target),
            'aligned_literal_pointer_file_offsets': [hex(i) for i in range(0, len(data)-3, 4)
                                                     if data[i:i+4] == packed],
        }
    blocks = {'gpio_helpers': (0x3268, 0x351c),
              'gpio27_controller': (0x54344, 0x543fc),
              'bitbang_and_register_io': (0x543fc, 0x552ac),
              'poe_poll_and_init': (0x552ac, 0x56a84),
              'device_configuration_table': (0xcb65c, 0xcb674)}
    return {
        'image_sha256': EXPECTED,
        'method': 'Original MIPS instructions with synthetic hardware plus static direct-reference inventory',
        'device_access': False,
        'blocks': {name: {'file_start': hex(a), 'file_end_exclusive': hex(b),
                          'sha256': hashlib.sha256(data[a:b]).hexdigest()}
                   for name, (a, b) in blocks.items()},
        'static_scan_file_intervals': [[hex(a), hex(b)] for a, b in RANGES],
        'references': refs,
        'initialization': {
            'entry_va': '0xbfc5e994',
            'mocked_calls': ['0xbf01a1dc: delay', '0xbfc101c0: platform helper',
                             '0xbfc5c7a8: successful register write',
                             '0xbfc5ca08: successful register read returning zero'],
            'i2c_address_table': list(data[0xcb670:0xcb674]),
            'register_value_pairs': init_table,
            'bus_writes_device_register_value': writes,
            'bus_reads_device_register': reads,
            'gpio_data_write_values': gpio_writes,
            'gpio27_after_init': get(c, 0xb800350c) >> 27 & 1,
        },
        'combined_poll': {'entry_va': '0xbfc5e2fc', 'cases_passed': len(cases),
                          'mocked_calls': ['0xbfc26828: LED force', '0xbfc26830: LED mode'],
                          'cases': cases},
        'limits': ['No physical fan speed, power or tachometer measurement',
                   'No PSE chip model established',
                   'Direct-reference and literal-pointer scan is not a proof against computed indirect calls',
                   'Synthetic bus replies do not establish actual device responses or register semantics',
                   'No conclusion about autonomous analog fan circuitry outside the CPU runtime'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.image.read_bytes()), indent=2) + '\n', end='')
