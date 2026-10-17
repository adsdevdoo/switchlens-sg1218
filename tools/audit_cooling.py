#!/usr/bin/env python3
"""Extract SHA-pinned GPIO/PoE evidence; no device access or firmware writes.

Physical fan wiring is not established by this audit. GPIO numbers below are
firmware bit indices, not connector pins or Linux GPIO line numbers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED = 'c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32'


def analyze(data):
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError('Unexpected image SHA-256')

    def witness(start, end):
        return {'file_start': hex(start), 'file_end_exclusive': hex(end),
                'sha256': hashlib.sha256(data[start:end]).hexdigest()}

    def immediate(offset):
        return struct.unpack_from('>I', data, offset)[0] & 0xffff

    low = immediate(0x543dc)
    high = immediate(0x543c8)
    assert (low, high) == (1460, 1501)
    return {
        'image_sha256': EXPECTED,
        'scope': 'Static code evidence; physical fan mapping unverified',
        'gpio_numbering': 'Bit indices in the firmware 32-bit GPIO register',
        'registers': {'control': '0xb8003500', 'direction': '0xb8003508',
                      'data': '0xb800350c'},
        'input_path': {
            'bit': 26, 'mask': '0x04000000',
            'setup': witness(0x5466c, 0x546a4),
            'reader': witness(0x3328, 0x334c),
            'consumer': witness(0x560a4, 0x56184),
            'consumer_behavior': 'Selects opposite force-mode values for LED outputs 26/27, index 0',
            'fan_alarm_polarity': None,
            'per_fan_identity': None,
        },
        'output_path': {
            'bit': 27, 'mask': '0x08000000',
            'setup': witness(0x5449c, 0x544f4),
            'output_wrapper': witness(0x54344, 0x54368),
            'register_writer': witness(0x32ec, 0x3328),
            'controller': witness(0x54368, 0x543fc),
            'state_ram': '0xbf014840',
            'consumption_ram': '0xbf014400',
            'sum_source': 'Signed 16-bit values at 0xbf0143e0 + 48*i + 10, inclusive configured first/last indices',
            'state_0_to_1_when_sum_less_than': low,
            'state_1_to_0_when_sum_at_least': high,
            'raw_power_unit_w': 0.1,
            'hold_previous_state_raw_interval_inclusive': [low, high - 1],
            'initial_output_level': 0,
            'physical_voltage_or_speed_for_each_level': None,
            'fan_mapping_verified': False,
        },
        'poll_chain': [
            {'file_offset': '0x56798', 'callee_va': '0xbfc5e2fc'},
            {'file_offset': '0x56314', 'callee_va': '0xbfc5e0a4'},
            {'file_offset': '0x5631c', 'callee_va': '0xbfc5c368'},
        ],
        'uart_read_commands': [
            'reg socget 0x3508',
            'reg socget 0x350c',
            'reg flashget 0x14840 0',
        ],
        'uart_read_implementation': {
            'socget': witness(0x259e8, 0x25a2c),
            'flashget_single_word': witness(0x25b44, 0x25ba0),
            'syntax': 'No -- prefix; flashget uses BF000000 OR offset, despite its name',
            'misleading_output': 'The single-word flashget read prints set flashreg; the selected path only loads',
        },
        'not_established': ['Fan-header connection to GPIO26/GPIO27',
                            'Fan alarm polarity or individual fan states',
                            'RPM source or tachometer pulse capture',
                            'Fan supply waveform/voltage and startup fault cause'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    args = parser.parse_args()
    try:
        result = analyze(args.image.read_bytes())
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
