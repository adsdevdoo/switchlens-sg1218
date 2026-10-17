#!/usr/bin/env python3
"""Build an experimental exact-image MIPS patch. Local files only; never flashes.

This produces a bench candidate, not a hardware-validated or production release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 'c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32'
START, END, BASE = 0xd8640, 0xf7000, 0xbfc08000
UART_PATCHES = [
    (0x25e94, '8c45f018', '24051fff', 'Enable the 13 stock CLI permission bits in RAM initialization'),
    (0x25ed8, '30420001', '24020001', 'Enable the existing runtime UART CLI dispatcher'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def jump(address, link=False):
    if address & 3 or address >> 28 != 0xb:
        raise ValueError('Invalid MIPS pseudo-direct jump destination')
    return struct.pack('>I', (0x0c000000 if link else 0x08000000) | ((address >> 2) & 0x3ffffff))


def package(original, payload, symbols, uart_cli=False, cooling_cli=False):
    if sha(original) != EXPECTED:
        raise ValueError('STOP: unexpected input image SHA-256')
    if not payload or len(payload) > END - START:
        raise ValueError('Payload empty or outside audited padding')
    if original[START:END] != b'\xff' * (END - START):
        raise ValueError('Candidate code region is not erased padding')
    sites = [(0x3425c, 0xbfc2bdd8, symbols['sg_route_compare'], True),
             (0x34280, 0xbfc4163c, symbols['sg_route_dispatch'], False)]
    if cooling_cli:
        if not uart_cli:
            raise ValueError('Cooling diagnostics require the runtime UART CLI')
        sites += [(0x24bb4, 0xbfc2c508, symbols['sg_cli_lookup'], True),
                  (0x25848, 0xbfc2c508, symbols['sg_cli_lookup'], True),
                  (0x25ee4, 0xbfc2cd0c, symbols['sg_cli_poll'], True)]
    output = bytearray(original)
    changes = []
    for offset, old, new, link in sites:
        if original[offset:offset+4] != jump(old, link):
            raise ValueError(f'Unexpected original instruction at {offset:#x}')
        if not BASE + START <= new < BASE + START + len(payload):
            raise ValueError('Hook destination is outside payload')
        replacement = jump(new, link)
        output[offset:offset+4] = replacement
        changes.append({'offset': hex(offset), 'before': jump(old, link).hex(), 'after': replacement.hex()})
    if uart_cli:
        for offset, before, after, purpose in UART_PATCHES:
            if original[offset:offset+4] != bytes.fromhex(before):
                raise ValueError(f'Unexpected original UART instruction at {offset:#x}')
            output[offset:offset+4] = bytes.fromhex(after)
            changes.append({'offset': hex(offset), 'before': before, 'after': after, 'purpose': purpose})
    if cooling_cli:
        offset = 0x54344
        before = bytes.fromhex('2c82000210400005')
        if original[offset:offset+8] != before:
            raise ValueError('Unexpected GPIO27 output helper prologue')
        target = symbols['sg_cool_output']
        if not BASE+START <= target < BASE+START+len(payload):
            raise ValueError('Cooling hook destination outside payload')
        after = jump(target) + b'\0'*4
        output[offset:offset+8] = after
        changes.append({'offset': hex(offset), 'before': before.hex(), 'after': after.hex(),
                        'purpose': 'Bounded GPIO27 override with stock automatic return'})
    output[START:START+len(payload)] = payload
    crc = zlib.crc32(output[0x10:END])
    output[:4] = struct.pack('>I', crc)
    allowed = [(0, 4), (START, START+len(payload))] + [(row[0], row[0]+4) for row in sites]
    if uart_cli:
        allowed += [(offset, offset+4) for offset, *_ in UART_PATCHES]
    if cooling_cli:
        allowed += [(0x54344, 0x5434c)]
    if len(output) != len(original):
        raise ValueError('Image size changed')
    changed = [i for i, (a, b) in enumerate(zip(original, output)) if a != b]
    if any(not any(a <= i < b for a, b in allowed) for i in changed):
        raise ValueError('Unexpected modification outside patch allowlist')
    return bytes(output), {
        'version': 'v0.1.2-cooling' if cooling_cli else 'experimental-1',
        'classification': 'DIAGNOSTIC_BUILD_AWAITING_HARDWARE_TEST' if cooling_cli else 'EXPERIMENTAL_UNTESTED_ON_HARDWARE',
        'input_sha256': EXPECTED, 'output_sha256': sha(output),
        'payload_sha256': sha(payload), 'image_bytes': len(output),
        'payload_bytes': len(payload), 'payload_file_offset': hex(START),
        'payload_va': hex(BASE+START), 'padding_remaining_bytes': END-START-len(payload),
        'crc32': f'{crc:08x}', 'crc_range': ['0x10', hex(END)],
        'changed_bytes': len(changed), 'hooks': changes,
        'uart_cli': bool(uart_cli),
        'cooling_cli': bool(cooling_cli),
        'uart_cli_scope': 'Stock runtime CLI including write/reset commands; not a bootloader recovery console' if uart_cli else 'Stock disabled CLI retained',
        'no_bootloader_modification': True, 'no_global_ram_allocation': True,
        'hardware_boot_test': False, 'recovery_test': False,
        'limitations': (['v0.1.2 installation and physical fan response not yet tested',
                         '100 raw IRQ ticks; wall-time unit unconfirmed',
                         'Software return requires running timer and cooperative event loop',
                         'No verified RPM/per-fan health measurement',
                         'Physical recovery and long-duration load remain untested'] if cooling_cli else ['Bootloader checks unknown', 'SPI dump and recovery required before lab flash',
                        'Stack/IRQ and socket timing require bench validation',
                        'MIB field semantics partly inferred from RTL838x sources']),
    }


def run(command):
    subprocess.run([str(arg) for arg in command], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--cc', default='mips-linux-gnu-gcc')
    parser.add_argument('--prefix', default='mips-linux-gnu-')
    parser.add_argument('--output', type=Path, default=ROOT/'build-target')
    parser.add_argument('--uart-cli', action='store_true', help='Enable stock runtime UART CLI for a diagnostic bench build')
    parser.add_argument('--cooling-cli', action='store_true', help='Add bounded GPIO27 tests and cooling JSON; requires --uart-cli')
    args = parser.parse_args()
    if args.cooling_cli and not args.uart_cli:
        parser.error('--cooling-cli requires --uart-cli')
    original = args.image.read_bytes()
    if sha(original) != EXPECTED:
        parser.error('STOP: unexpected input image SHA-256; build not started')
    out = args.output.resolve()
    image_out = out/'SwitchLens-SG1218MPE-V5-experimental.bin'
    if image_out == args.image.resolve():
        parser.error('STOP: output must not overwrite the input firmware')
    out.mkdir(parents=True, exist_ok=True)
    flags = ['-std=c99', '-Os', '-Wall', '-Wextra', '-Werror', '-ffreestanding',
             '-fno-builtin', '-fno-pic', '-fno-pie', '-fno-stack-protector',
             '-fno-asynchronous-unwind-tables', '-fno-unwind-tables',
             '-fno-common', '-fstack-usage', '-ffunction-sections', '-fdata-sections',
             '-mabi=32', '-mips32r2', '-msoft-float', '-mno-abicalls', '-G0', '-EB', '-Iinclude']
    sources = ['target/route.S', 'target/adapter.c', 'target/runtime.c', 'src/sg_stats.c', 'src/sg_mib.c']
    if args.cooling_cli:
        flags += ['-DSG_COOLING']
        sources += ['target/cooling.c']
    objects = []
    for source in sources:
        obj = out/(Path(source).stem+'.o')
        run([args.cc, *flags, '-c', source, '-o', obj])
        objects.append(obj)
    elf, binary = out/'switchlens.elf', out/'payload.bin'
    extra = ['--undefined='+s for s in ['sg_cli_lookup','sg_cli_poll','sg_cool_output']] if args.cooling_cli else []
    run([args.prefix+'ld.bfd', *extra, '-EB', '-T', 'target/firmware.ld', '--gc-sections',
         '--undefined=sg_route_dispatch', '--build-id=none', '-Map='+str(out/'switchlens.map'),
         '-o', elf, *objects])
    run([args.prefix+'objcopy', '-O', 'binary', elf, binary])
    with elf.open('rb') as stream:
        parsed = ELFFile(stream)
        if parsed.little_endian or parsed.elfclass != 32 or parsed['e_machine'] != 'EM_MIPS':
            raise ValueError('Unexpected ELF architecture')
        table = parsed.get_section_by_name('.symtab')
        symbols = {symbol.name: symbol['st_value'] for symbol in table.iter_symbols() if symbol.name}
        undefined = [s.name for s in table.iter_symbols() if s.name and s['st_shndx'] == 'SHN_UNDEF']
        if undefined:
            raise ValueError('Unresolved symbols: '+','.join(undefined))
        for section in parsed.iter_sections():
            if section['sh_flags'] & 2 and section['sh_size']:
                if section['sh_flags'] & 1 or section['sh_type'] == 'SHT_NOBITS':
                    raise ValueError('Unexpected writable/loadable zero-fill section')
                if not BASE+START <= section['sh_addr'] < section['sh_addr']+section['sh_size'] <= BASE+END:
                    raise ValueError('Allocated section exceeds padding')
    patched, manifest = package(original, binary.read_bytes(), symbols, uart_cli=args.uart_cli, cooling_cli=args.cooling_cli)
    manifest['compiler'] = subprocess.check_output([args.cc, '--version'], text=True).splitlines()[0]
    manifest['linker'] = subprocess.check_output([args.prefix+'ld.bfd', '--version'], text=True).splitlines()[0]
    manifest['build_recipe_sha256'] = sha(Path(__file__).read_bytes())
    manifest['compiler_flags'] = flags
    manifest['sources_sha256'] = {name: sha((ROOT/name).read_bytes()) for name in sources+[
        'target/firmware.ld', 'include/sg_stats.h', 'include/sg_fields.h', 'include/sg_mib.h', 'src/sg_fields.inc'] + (['target/cooling.h'] if args.cooling_cli else [])}
    manifest['symbols'] = {name: hex(address) for name, address in symbols.items() if name.startswith(('sg_', 'fw_'))}
    image_out.write_bytes(patched)
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k: manifest[k] for k in ('classification','output_sha256','payload_bytes','changed_bytes')}, indent=2))


if __name__ == '__main__':
    main()
