#!/usr/bin/env python3
"""Read-only, SHA-pinned extraction of startup, timer and update evidence.

This is a focused static audit, NOT a bootloader emulator or a flashability test.
All intervals are half-open file/virtual-address ranges. No device is accessed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

EXPECTED = 'c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32'
FLASH_VA = 0xbfc08000


def analyze(data):
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED:
        raise ValueError('Unexpected image SHA-256; no analysis performed')

    def word(offset):
        return struct.unpack_from('>I', data, offset)[0]

    def imm(offset):
        value = word(offset) & 0xffff
        return value - 0x10000 if value & 0x8000 else value

    def pair(offset):
        """Decode adjacent LUI + ADDIU/ORI to the same register."""
        hi, lo = word(offset), word(offset + 4)
        register = (hi >> 16) & 31
        if hi >> 26 != 15 or (hi >> 21) & 31:
            raise ValueError(f'Expected LUI at {offset:#x}')
        if (lo >> 21) & 31 != register or (lo >> 16) & 31 != register:
            raise ValueError(f'Expected matching registers at {offset:#x}')
        high = (hi & 0xffff) << 16
        if lo >> 26 == 9:
            return (high + imm(offset + 4)) & 0xffffffff
        if lo >> 26 == 13:
            return high | (lo & 0xffff)
        raise ValueError(f'Expected ADDIU/ORI at {offset + 4:#x}')

    def interval(start, end):
        return {'start': hex(start), 'end_exclusive': hex(end), 'bytes': end - start}

    vectors_ram = pair(0x620)
    vectors_rom, vectors_rom_end = pair(0x628), pair(0x630)
    initialized_ram = pair(0x64c)
    initialized_rom, initialized_last = pair(0x65c), pair(0x664)
    bss_first, bss_last = pair(0x684), pair(0x68c)
    code_first, code_rom, code_end = pair(0x6a4), pair(0x6ac), pair(0x6b4)
    # These loops have different termination order. See startup disassembly:
    # 0x670 pre-increments its source before the equality test; 0x698 clears
    # the final word in the branch delay slot. Their one-word overlaps are real.
    initial_sp = ((word(0x6e0) & 0xffff) << 16) + ((word(0x6e4) & 0xffff) << 16) - imm(0x6ec)
    control = ((word(0x84c0) & 0xffff) << 16) | (word(0x84c8) & 0xffff)
    timer_base = (pair(0x84b0) << 4) & 0xffffffff
    period = imm(0x84e4)
    if period != imm(0x84f4):
        raise ValueError('Timer branches disagree')
    divider = control & 0xffff
    software_divider = imm(0x3cd4)
    crc_start, crc_end = 0x10, 0xf7000
    crc_actual = zlib.crc32(data[crc_start:crc_end])
    padding_start = 0xd8640
    frames = []
    for start, end in ((0x3160, 0x8178), (0x8178, 0x91700)):
        for offset in range(start, end, 4):
            if word(offset) >> 16 == 0x27bd and imm(offset) < 0:
                frames.append({'file_offset': hex(offset), 'frame_bytes': -imm(offset)})
    frames.sort(key=lambda row: row['frame_bytes'], reverse=True)

    return {
        'image_sha256': digest,
        'status': 'verified_static; not hardware validation; no flashability decision',
        'image_size': len(data),
        'header_be_u32': [hex(word(i)) for i in range(0, 16, 4)],
        'crc32': {'range': interval(crc_start, crc_end), 'computed': hex(crc_actual),
                  'stored': hex(word(0)), 'matches': crc_actual == word(0)},
        'candidate_code_padding': {
            **interval(padding_start, crc_end),
            'all_ff': all(value == 255 for value in data[padding_start:crc_end]),
            'allocation_proven_safe': False,
        },
        'startup': {
            'evidence_file': interval(0x620, 0x708),
            'vectors_file': interval(vectors_rom - FLASH_VA, vectors_rom_end - FLASH_VA),
            'vectors_ram': interval(vectors_ram, vectors_ram + vectors_rom_end - vectors_rom),
            'initialized_copy_file': interval(initialized_rom - FLASH_VA, initialized_last - FLASH_VA + 4),
            'initialized_copy_ram': interval(initialized_ram, initialized_ram + initialized_last - initialized_rom + 4),
            'zeroed_ram_including_last_word': interval(bss_first, bss_last + 4),
            'ram_code_file': interval(code_rom - FLASH_VA, code_rom - FLASH_VA + code_end - code_first),
            'ram_code': interval(code_first, code_end),
            'initial_sp': hex(initial_sp),
            'code_to_initial_sp': interval(code_end, initial_sp),
            'overlap_note': 'Last initialized word is zeroed; last zeroed word is overwritten by RAM code',
            'free_ram_bytes': None,
            'largest_sp_adjustments': frames[:8],
            'stack_note': 'Instruction scan, NOT a call-graph or interrupt stack bound',
        },
        'timer': {
            'init_file': interval(0x84b0, 0x8544),
            'init_call_file': interval(0x86c4, 0x86d4),
            'isr_file': interval(0x3ccc, 0x3dec),
            'base_for_index_zero': hex(timer_base), 'control_initial': hex(control),
            'hardware_divider': divider, 'data_value': period,
            'software_divider': software_divider,
            'raw_counter_ram': '0xbf002e90', 'raw_counter_bits': 32,
            'hypothesis_lxb_hz': 200_000_000,
            'conditional_irq_seconds': divider * period / 200_000_000,
            'conditional_raw_unit_seconds': divider * period * software_divider / 200_000_000,
            'actual_clock_confirmed': False, 'export_uptime_seconds': None,
        },
        'signcheck_dataflow': {
            'status': 'verified_static_by_manual_disassembly; witnesses below',
            'uid_copy': {'file_offset': '0x45778', 'callee_va': '0xbfc1044c',
                         'source_ram': '0xbf016a9c', 'length_ram': '0xbf002e80', 'destination': 'sp+0x18'},
            'saved_uid_length': {'file_offset': '0x457c8', 'destination': 'sp+0x500'},
            'sha1_update': {'file_offset': '0x46088', 'callee_va': '0xbf01e1c8',
                            'input': 'sp+0x18', 'length': 'word at sp+0x500'},
            'signature_storage_va': interval(0xb41fc006, 0xb41fc086),
            'scope': 'This SignCheck hashes the UID; does not prove absence of bootloader image verification',
        },
        'upgrade_handoff': {
            'status': 'verified_static; subsequent loader behavior unknown',
            'staging_va': '0xb4100000', 'crc_call_file': '0x3602c',
            'zero_header_write_call_file': '0x36060', 'zero_header_destination_va': '0xb4008000',
            'zero_header_bytes': 16, 'countdown_ram': '0xbf0013e0', 'countdown_value': 7,
            'countdown_handler_file': interval(0x30048, 0x300e0),
            'bootloader_in_input': False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    try:
        result = analyze(args.image.read_bytes())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
