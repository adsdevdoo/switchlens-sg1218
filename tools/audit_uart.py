#!/usr/bin/env python3
"""Read-only, SHA-pinned witnesses for the stock UART CLI dispatch gate.

Usage: python3 tools/audit_uart.py backups/original/2026-10-17/GD25Q16B-xgpro-original.bin
Prints JSON. Does not patch firmware, connect to hardware, or write files.
"""
import argparse
import hashlib
import json
from pathlib import Path

DUMP_SHA256 = "b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87"
IMAGE_SHA256 = "c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32"
IMAGE_SIZE = 1013324
GATE_OFFSET = 0x25EC8
GATE_BYTES = bytes.fromhex(
    "27bdffe8 afbf0014 3c02bfd0 8c42f018 30420001 10400004 8fbf0014 "
    "0ff0b343 00002021 8fbf0014 00001021 03e00008 27bd0018"
)


def audit(data):
    digest = hashlib.sha256(data).hexdigest()
    if digest != DUMP_SHA256 or len(data) != 2097424:
        raise ValueError("Unexpected dump SHA-256 or size")
    images = [data[start:start + IMAGE_SIZE] for start in (0x8000, 0x100000)]
    for image in images:
        if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
            raise ValueError("Unexpected embedded runtime image")
        if image[GATE_OFFSET:GATE_OFFSET + len(GATE_BYTES)] != GATE_BYTES:
            raise ValueError("CLI dispatcher witness does not match")
    image = images[0]
    # Decode the actual LUI/LW/ANDI/BEQ/JAL words in the pinned binary.
    words = [int.from_bytes(GATE_BYTES[i:i+4], "big")
             for i in range(0, len(GATE_BYTES), 4)]
    low = words[3] & 0xFFFF
    low = low - 0x10000 if low & 0x8000 else low
    flag_va = (((words[2] & 0xFFFF) << 16) + low) & 0xFFFFFFFF
    flag_offset = flag_va - 0xBFC08000
    mask = words[4] & 0xFFFF
    flag = int.from_bytes(image[flag_offset:flag_offset+4], "big")
    branch_va = 0xBFC08000 + GATE_OFFSET + 5 * 4
    target = branch_va + 4 + 4 * (words[5] & 0xFFFF)
    callee = ((branch_va + 4) & 0xF0000000) | ((words[7] & 0x03FFFFFF) << 2)
    assert image[0xD37B0:0xD37B6] == b"RTK# \x00"
    return {
        "status": "verified_static; not a hardware RX or recovery test",
        "dump_sha256": digest,
        "runtime_sha256": IMAGE_SHA256,
        "runtime_copies_spi_offsets": ["0x8000", "0x100000"],
        "cli_dispatcher": {
            "runtime_file_offset": hex(GATE_OFFSET),
            "va": hex(0xBFC08000 + GATE_OFFSET),
            "bytes_hex": GATE_BYTES.hex(),
            "flag_va": hex(flag_va),
            "flag_runtime_file_offset": hex(flag_offset),
            "flag_spi_offsets": [hex(start + flag_offset) for start in (0x8000, 0x100000)],
            "flag_word_be": hex(flag),
            "enable_mask": hex(mask),
            "enabled_in_saved_image": bool(flag & mask),
            "disabled_branch_target_va": hex(target),
            "gated_cli_handler_va": hex(callee),
            "flag_inside_known_runtime_crc_range": 0x10 <= flag_offset < 0xF7000,
        },
        "manual_disassembly_witnesses": {
            "dispatcher_registration_runtime_range": ["0x26988", "0x2699c"],
            "handler_poll_getc_runtime_range": ["0x24dd8", "0x24df8"],
            "handler_cr_lf_and_prompt_runtime_range": ["0x24df8", "0x24e3c"],
            "prompt_runtime_file_offset": "0xd37b0",
            "boot_normal_handoff_spi_range": ["0x1730", "0x17c0"],
        },
        "limits": [
            "Static gate result does not prove physical RX wiring or solder joints.",
            "No universal absence of alternative console or recovery paths is claimed.",
            "No firmware modification or hardware write is performed.",
            "Flag is outside the known runtime CRC range; update acceptance and persistence are not established.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.dump.read_bytes())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
