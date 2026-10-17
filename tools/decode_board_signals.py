#!/usr/bin/env python3
"""Decode one copied UART observation into JSON; no serial/network/device access.

Input must contain exactly one result for each documented read command. Repeated
addresses are rejected so separate observations cannot be silently mixed.
This output is a diagnostic record, not the /stats.json API or measured fan RPM.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ADDRESSES = {0xb8003508, 0xb800350c, 0xbf014840}
LINE = re.compile(r'\b(get socreg|(?:get|set) flashreg)\s+0x([0-9a-f]+)\s*=\s*0x([0-9a-f]+)', re.I)


def decode(text, label=None):
    values = {}
    for match in LINE.finditer(text):
        kind, address, value = match.groups()
        address, value = int(address, 16), int(value, 16)
        if address not in ADDRESSES:
            continue
        if value > 0xffffffff:
            raise ValueError('Register value exceeds 32 bits')
        if address in values:
            raise ValueError(f'Repeated address {address:#x}; use one observation per file')
        if (address == 0xbf014840) != ('flashreg' in kind.lower()):
            raise ValueError('Unexpected read-result type for address')
        values[address] = value
    if values.keys() != ADDRESSES:
        missing = ', '.join(hex(a) for a in sorted(ADDRESSES - values.keys()))
        raise ValueError('Missing read results: ' + missing)
    direction, data, state = (values[a] for a in (0xb8003508, 0xb800350c, 0xbf014840))
    return {
        'diagnostic_version': 1,
        'source': 'copied_uart_text',
        'label': label,
        'capture_time': None,
        'atomic_snapshot': False,
        'registers_raw': {f'0x{a:08x}': f'0x{values[a]:08x}' for a in sorted(values)},
        'signals': {
            'gpio26_level_raw': (data >> 26) & 1,
            'gpio27_level_raw': (data >> 27) & 1,
            'gpio26_configured_as_input': not bool(direction & (1 << 26)),
            'gpio27_configured_as_output': bool(direction & (1 << 27)),
            'poe_load_control_state_raw': state,
            'poe_load_control_state_valid': state in (0, 1),
            'output_matches_state': ((data >> 27) & 1) == state if state in (0, 1) else None,
        },
        'fan_mapping_verified': False,
        'fan_status': None,
        'fan_rpm': None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='UTF-8 UART text file, or - for stdin')
    parser.add_argument('--label', help='Operator description of this observation')
    args = parser.parse_args()
    try:
        source = sys.stdin.read() if args.input == '-' else Path(args.input).read_text(encoding='utf-8-sig')
        result = decode(source, args.label)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
