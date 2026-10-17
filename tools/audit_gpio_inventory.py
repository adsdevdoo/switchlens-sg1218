#!/usr/bin/env python3
"""Bounded, offline stock GPIO inventory; never connects to the switch.

References are syntactic evidence, not an exhaustive indirect-call proof.
Execute selected original routines with explicitly mocked peripheral replies.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_MEM_WRITE
from audit_cooling_paths import (EXPECTED, RANGES, call, direct_refs, get,
                                 machine, put, stub)

HELPERS = {
    0xbf019630: 'SoC mux', 0xbf019678: 'SoC direction',
    0xbf0196b4: 'SoC data write', 0xbf0196f0: 'SoC data read',
    0xbf019714: 'alternate mux', 0xbf019750: 'alternate direction',
    0xbf01978c: 'alternate data write', 0xbf0197c8: 'alternate data read',
    0xbf0197ec: 'alternate mux', 0xbf019828: 'alternate direction',
    0xbf019864: 'alternate data write', 0xbf0198a0: 'alternate data read',
    0xbfc24588: 'external GPIO data-set wrapper',
    0xbfc125a8: 'dal_maple_extGpio_pin_data_set',
    0xbfc24590: 'external GPIO data-get wrapper',
    0xbfc24598: 'external GPIO direction-set wrapper',
    0xbfc245a8: 'external GPIO device-enable wrapper',
    0xbfc245b0: 'external raw register-write wrapper',
    0xbfc245b8: 'external raw register-read wrapper',
    0xbfc245c0: 'RTL8231 initialization wrapper',
}


def word(data, off):
    return struct.unpack_from('>I', data, off)[0]


def pairs(data, targets):
    """Candidate LUI + ADDIU/ORI pairs <=8 words apart, same source register.

    Deliberately ignores control flow and intervening overwrites: a hit needs
    review and is not evidence that the value is used as a function pointer.
    """
    found = {target: [] for target in targets}
    for start, end in RANGES:
        for off in range(start, end, 4):
            first = word(data, off)
            if first >> 26 != 15:
                continue
            reg = first >> 16 & 31
            upper = (first & 0xffff) << 16
            for next_off in range(off + 4, min(off + 36, end), 4):
                second = word(data, next_off)
                op, source, low = second >> 26, second >> 21 & 31, second & 0xffff
                if source != reg or op not in (9, 13):
                    continue
                value = ((upper + (low if low < 0x8000 else low - 0x10000))
                         if op == 9 else upper | low) & 0xffffffff
                if value in found:
                    found[value].append([hex(off), hex(next_off)])
    return found


def analyze(data):
    assert hashlib.sha256(data).hexdigest() == EXPECTED, 'Unexpected image'
    candidates = pairs(data, HELPERS)
    references = {
        hex(address): {
            'role': name, 'direct_j_jal_file_offsets': direct_refs(data, address),
            'aligned_literal_file_offsets': [hex(i) for i in range(0, len(data)-3, 4)
                                              if word(data, i) == address],
            'nearby_lui_pair_candidates': candidates[address],
        } for address, name in HELPERS.items()
    }

    # Run the formerly mocked helper with real instructions and synthetic MMIO.
    platform_cases = []
    for initial in (0, 0xffffffff, 0xa5a55a5a):
        c = machine(data)
        c.uc.mem_map(0x1b000000, 0x10000)
        for addr in (0xb8003500, 0xb8003508, 0xb800350c):
            put(c, addr, initial)
        writes = []
        c.uc.hook_add(UC_HOOK_MEM_WRITE,
                      lambda uc, ac, addr, size, value, unused:
                      writes.append([hex(addr), hex(value)]),
                      begin=0x18003500, end=0x1800350f)
        call(c, 0xbfc101c0)
        assert get(c, 0xb8003500) == initial & ~0x180000
        assert get(c, 0xb8003508) == initial & ~0x180000
        assert get(c, 0xb800350c) == initial
        platform_cases.append({'initial_gpio_registers': hex(initial), 'writes': writes,
                               'data_unchanged': True})

    # Default board config lives in the update at file 0xf7000 and is copied
    # from flash 0xb40ff000. Replace only the unrelated MAC getter with zeros.
    c = machine(data)
    c.uc.mem_map(0x14000000, 0x200000)
    c.uc.mem_write(0x14008000, data)
    put(c, 0xbf002e88, 0xb40ff000)
    stub(c, 0xbfc54018, lambda a: c.uc.mem_write(a[0] & 0x1fffffff, bytes(6)))
    call(c, 0xbfc30d44, 0)
    default_config = {hex(off): hex(get(c, 0xbf00e660 + off)) for off in
                      (0x40, 0x44, 0x88, 0x1a8, 0x1ac, 0x1b0, 0x1b4, 0x1b8,
                       0x4e4, 0x4e8)}
    assert default_config['0x1a8'] == '0x0'
    assert default_config['0x4e4'] == '0x0'
    masked_rows = [[get(c, 0xbf00e660 + 0x4fc + row*32 + col*4)
                    for col in range(8)] for row in range(6)]
    assert all(row[0] == 0 for row in masked_rows)

    # Owner boot log says PHY c984. Execute its board-selector branch.
    stub(c, 0xbfc26e90, lambda a: put(c, a[3], 0xc984))
    stub(c, 0xbfc11514)  # logging only
    call(c, 0xbfc2eba8, 0)
    board_id = get(c, 0xbf00e660 + 0x44)
    assert board_id == 0x43
    call(c, 0xbfc92440, 0, board_id)

    # Execute board-specific port/GPIO setup including actual external GPIO
    # direction/enable code; mock only its low-level 16-bit register transport.
    registers, bus = {}, []

    def read_ext(args):
        unit, device, reg, output = args
        value = registers.get((unit, device, reg), 0)
        put(c, output, value)
        bus.append({'op': 'read', 'device': device, 'reg': reg, 'value': value})

    def write_ext(args):
        unit, device, reg, value = args
        registers[unit, device, reg] = value
        bus.append({'op': 'write', 'device': device, 'reg': reg, 'value': value})

    stub(c, 0xbfc12470, read_ext)
    stub(c, 0xbfc12380, write_ext)
    call(c, 0xbfc29550, 0)
    writes = [item for item in bus if item['op'] == 'write']
    assert sorted({item['reg'] for item in writes}) == [0, 2, 3, 4, 5, 6]
    assert registers[0, 0, 5] == sum(1 << bit for bit in (8, 9, 3, 4, 13, 14))
    assert registers[0, 0, 6] == (1 << 8) | (1 << 9)
    table_off = 0xbf0008f0 - 0xbf000400 + 0x720
    table = [list(struct.unpack_from('>9I', data, table_off + 36*i)) for i in range(4)]

    # The PHY-selected board takes the internal GPIO media-selection branch.
    # Execute it with the owner's earlier data word, stubbing only port setters.
    c.uc.mem_map(0x1b000000, 0x10000)
    put(c, 0xb800350c, 0x39780000)
    media_calls, external_poll_calls = [], []
    stub(c, 0xbfc27500)
    stub(c, 0xbfc27510, lambda a: media_calls.append(a[:3]))
    stub(c, 0xbfc28da4, lambda a: external_poll_calls.append(a))
    call(c, 0xbfc293c8, 0)
    assert media_calls == [[0, 24, 0], [0, 25, 0], [0, 26, 1], [0, 27, 1]]
    assert not external_poll_calls

    # Decode all 32 bits in the previously supplied CLI snapshot. This is not
    # a new device read. A register bit is not a connector/ASIC package pin.
    cnr, direction, levels = 0xc2e7ff00, 0x39000000, 0x39780000
    pins = [{'gpio': pin, 'cnr_bit': cnr >> pin & 1,
             'direction_bit': direction >> pin & 1, 'data_bit': levels >> pin & 1,
             'mode': 'alternate' if cnr >> pin & 1 else
                     'gpio_output' if direction >> pin & 1 else 'gpio_input'}
            for pin in range(32)]
    mmio_values = [base + offset for base in (0xb8000000, 0x98000000, 0x18000000)
                   for offset in range(0x3500, 0x3520, 4)]
    blocks = {'soc_helpers': (0x3268, 0x34fc), 'platform_setup': (0x81c0, 0x8270),
              'ext_gpio_driver': (0xa380, 0xade4), 'port_gpio_tables': (0xc10, 0xcf0),
              'port_gpio_paths': (0x20afc, 0x21760),
              'default_board_config': (0xf7000, 0xf764c)}
    return {
        'image_sha256': EXPECTED, 'device_access': False,
        'scan_intervals': [[hex(a), hex(b)] for a, b in RANGES],
        'blocks': {name: {'start': hex(a), 'end_exclusive': hex(b),
                          'sha256': hashlib.sha256(data[a:b]).hexdigest()}
                   for name, (a, b) in blocks.items()},
        'helper_references': references,
        'gpio_mmio_aligned_literals': [[hex(i), hex(word(data, i))]
                                      for i in range(0, len(data)-3, 4)
                                      if word(data, i) in mmio_values],
        'gpio_mmio_lui_pair_candidates': {hex(target): locations
                                         for target, locations in pairs(data, mmio_values).items()
                                         if locations},
        'platform_helper': {'entry': '0xbfc101c0', 'mocked_calls': [],
                            'cases': platform_cases},
        'default_config': {'entry': '0xbfc30d44', 'flash_address': '0xb40ff000',
                           'mocked_calls': ['0xbfc54018: MAC getter returns six zero bytes'],
                           'selected_fields': default_config,
                           'six_masked_initialization_rows': masked_rows},
        'board_selection': {'entry': '0xbfc2eba8', 'synthetic_phy_id': '0xc984',
                            'result_board_id': hex(board_id),
                            'mocked_calls': ['0xbfc26e90: PHY read returns 0xc984',
                                             '0xbfc11514: logging']},
        'external_gpio_port_init': {
            'entry': '0xbfc29550', 'board_id': hex(board_id),
            'mocked_calls': ['0xbfc12470: external register read',
                            '0xbfc12380: external register write'],
            'table_ram_address': '0xbf0008f0', 'table_rows': table,
            'input_pins_by_internal_port': {'24': [8, 9], '25': [3, 4],
                                             '26': [24, 25], '27': [13, 14]},
            'transactions': bus,
            'written_registers': sorted({item['reg'] for item in writes}),
            'output_data_registers_written': False,
        },
        'port_media_poll': {'entry': '0xbfc293c8', 'board_id': hex(board_id),
                            'gpio_data': '0x39780000', 'mode_calls': media_calls,
                            'external_poll_calls': external_poll_calls,
                            'mocked_calls': ['0xbfc27500: port setter',
                                             '0xbfc27510: media setter',
                                             '0xbfc28da4: external media poll (not reached)',
                                             '0xbfc11514: logging']},
        'owner_snapshot': {'cnr': hex(cnr), 'dir': hex(direction), 'data': hex(levels),
                           'pins': pins},
        'limits': [
            'Bounded static search; not proof that all indirect/computed paths are resolved',
            'Nearby LUI pairs are syntactic candidates, not executed pointer references',
            'Board config is the stock default, not a current RAM dump',
            'Peripheral replies are synthetic; RTL8231 driver presence does not identify a physical chip',
            'No physical fan wiring, voltage, RPM or fault polarity established',
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.image.read_bytes()), indent=2))
