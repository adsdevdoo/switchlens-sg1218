**English** | [Русский](UART-CONSOLE.ru.md)

# Stock UART console: code present, dispatcher disabled

**Current hardware result, 17 October 2026:** v0.1.1 was installed through stock
web upgrade, displayed RTK#, accepted help and returned the command list; two
JSON replies followed. [Texts and screenshots](../docs/evidence/2026-10-17-switchlens/README.md).
The analysis below explains the original stock silence; it was performed before
that hardware test.

## Finding and source bytes

The runtime contains CLI handler/prompt, but its periodic callback is gated by
bit 0 of `0xbfcff018`, which is **0x00000000** in the saved original image.
The observed branch returns before UART input polling or Enter processing.
Silence on that path therefore did not diagnose RX, pin 2 contact or R41/R42
soldering. Later help establishes the current two-way path; repeated resoldering
based solely on the earlier silence was not justified.

Original [SPI export](../backups/original/2026-10-17/README.md), SHA-256
`b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87`.
Its runtime copies at SPI `0x8000` and `0x100000` both match the 1,013,324-byte
vendor update BIN, SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
Runtime file offsets include the update header; SPI offsets start at the full dump.

## Traced path

1. File `0x26988..0x2699c` registers callback `0xbfc2dec8` through `0xbfc2df70`.
2. The callback reads the gate word, checks bit 0 and skips `0xbfc2cd0c` when zero.
3. CLI file `0x24dd8..0x24df8` polls `0xbfc1146c` and reads `0xbfc1147c`, wrappers
   leading to UART status/data. The disabled dispatcher never reaches this path.
4. `0x24df8..0x24e3c` handles LF/CR, including the empty-line `RTK# ` prompt,
   stored at file `0xd37b0`.

```text
file offset  VA          instruction
0x25ed0      bfc2ded0    lui   v0, 0xbfd0
0x25ed4      bfc2ded4    lw    v0, -0xfe8(v0)   # 0xbfcff018
0x25ed8      bfc2ded8    andi  v0, v0, 1
0x25edc      bfc2dedc    beqz  v0, 0xbfc2def0
0x25ee0      bfc2dee0    lw    ra, 0x14(sp)     # delay slot
0x25ee4      bfc2dee4    jal   0xbfc2cd0c
0x25ee8      bfc2dee8    move  a0, zero
0x25ef0      bfc2def0    move  v0, zero
0x25ef4      bfc2def4    jr    ra
0x25ef8      bfc2def8    addiu sp, sp, 0x18
```

| Item | Offset/value |
| --- | --- |
| Update-BIN gate word | `0xf7018`: `00 00 00 00` |
| First SPI runtime copy | `0xff018`: `00 00 00 00` |
| Second SPI runtime copy | `0x1f7018`: `00 00 00 00` |
| Runtime CRC coverage | `[0x10,0xf7000)`, gate word outside |

`0xbfc2de90` also decodes the same word into command permissions. Enabling only
the periodic gate does not prove all commands are enabled or recovery works.
v0.1.1 patches both initialization and dispatch instructions within CRC coverage,
leaving the parameter word unchanged. [Release details](../releases/v0.1.1-experimental-uart/README.md).

## Bootloader boundary

Normal boot SPI `0x1730..0x17c0`, RAM `0xbf003038..0xbf0030c8`, prints check
runtime img, validates header, prints address and jumps to `0xb4008010`.
This block does not wait for Enter or present a menu. Input helpers elsewhere
do not prove an accessible menu. Absence of every alternative stop/recovery path
is not asserted.

## Current next step

The modified runtime and help now work; JSON also works. Continue with loaded
PoE and metric verification. Runtime CLI does not establish emergency recovery.
The owner declined another desoldering exercise as a preliminary test. Original
dump and earlier firmware packages remain unchanged.

```bash
python3 tools/audit_uart.py backups/original/2026-10-17/GD25Q16B-xgpro-original.bin
```

The audit reads files only, checks SHA/both runtime copies/instructions and emits
gate address/value/mask. [Machine evidence](uart-console-evidence.json).
Capstone 5.0.9 with the documented RAM/flash map was used for static analysis;
that method is distinct from hardware observation.
