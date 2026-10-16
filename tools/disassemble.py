#!/usr/bin/env python3
"""Read-only MIPS32 BE disassembly of a SHA256-pinned local update image."""
import argparse
import hashlib
from pathlib import Path
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_BIG_ENDIAN

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('image', type=Path)
parser.add_argument('start', type=lambda s: int(s, 0))
parser.add_argument('end', type=lambda s: int(s, 0))
args = parser.parse_args()
data = args.image.read_bytes()
expected = 'c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32'
if hashlib.sha256(data).hexdigest() != expected:
    parser.error('Unexpected image SHA-256')
if not (0 <= args.start < args.end <= len(data)) or args.start % 4 or args.end % 4:
    parser.error('Expected an aligned, nonempty in-file interval')
ram_start, ram_end = 0x3160, 0x8178
if args.start < ram_start < args.end or args.start < ram_end < args.end:
    parser.error('Split the interval at RAM-copy mapping boundaries')
va = args.start - ram_start + 0xbf019528 if ram_start <= args.start < ram_end else args.start + 0xbfc08000
md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_BIG_ENDIAN)
md.skipdata = True
print('SHA256', expected)
for item in md.disasm(data[args.start:args.end], va):
    off = args.start + item.address - va
    print(f'{off:08x} {item.address:08x} {item.bytes.hex():8s} {item.mnemonic:8s} {item.op_str}')
