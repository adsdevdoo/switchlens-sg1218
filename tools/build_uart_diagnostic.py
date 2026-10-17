#!/usr/bin/env python3
"""Repackage the pinned v0.1.0 payload with UART CLI enabled; never flashes.

Reuses the byte-identical, previously built payload to avoid needing a cross
compiler. A from-source equivalent is build_firmware.py --uart-cli.
"""
import argparse
import json
from pathlib import Path

import build_firmware as builder

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'releases/v0.1.0-experimental'
BASE_SHA256 = '58d48cf69cac4024eddfb4ede1bb5a925420521a0f0e44011ff4fa08940c2e25'
FILENAME = 'SwitchLens-SG1218MPE-V5-experimental.bin'


def build():
    original_path = ROOT / 'vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin'
    original = original_path.read_bytes()
    released = (RELEASE / 'SwitchLens-SG1218MPE-V5-v0.1.0-experimental.bin').read_bytes()
    if builder.sha(released) != BASE_SHA256:
        raise ValueError('Unexpected base release SHA-256')
    previous = json.loads((RELEASE / 'build-manifest.json').read_text())
    if previous['output_sha256'] != BASE_SHA256:
        raise ValueError('Base manifest does not describe the pinned release')
    payload = released[builder.START:builder.START + previous['payload_bytes']]
    if builder.sha(payload) != previous['payload_sha256']:
        raise ValueError('Base payload hash mismatch')
    symbols = {name: int(address, 16) for name, address in previous['symbols'].items()}
    baseline, _ = builder.package(original, payload, symbols)
    if baseline != released:
        raise ValueError('The baseline release cannot be reproduced from its manifest')
    patched, manifest = builder.package(original, payload, symbols, uart_cli=True)
    manifest.update({
        'version': 'v0.1.1-experimental-uart',
        'base_release_sha256': BASE_SHA256,
        'payload_reused_without_recompilation': True,
        'payload_compiler': previous['compiler'],
        'payload_linker': previous['linker'],
        'payload_sources_sha256': previous['sources_sha256'],
        'symbols': previous['symbols'],
        'build_recipe_sha256': builder.sha(Path(__file__).read_bytes()),
        'packager_sha256': builder.sha((ROOT / 'tools/build_firmware.py').read_bytes()),
    })
    return patched, payload, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build-uart-diagnostic')
    args = parser.parse_args()
    out = args.output.resolve()
    protected = [ROOT / 'vendor', ROOT / 'backups', RELEASE]
    if any(out == p or p in out.parents for p in protected):
        parser.error('Output must not overwrite archived firmware or the original release')
    image, payload, manifest = build()
    out.mkdir(parents=True, exist_ok=True)
    (out / FILENAME).write_bytes(image)
    (out / 'payload.bin').write_bytes(payload)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ['version', 'output_sha256', 'uart_cli', 'hardware_boot_test', 'recovery_test']}, indent=2))


if __name__ == '__main__':
    main()
