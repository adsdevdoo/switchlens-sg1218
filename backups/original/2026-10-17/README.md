**English** | [Русский](README.ru.md)

# Original GD25Q16B export — first supplied read

Saved at the owner's explicit request on 17 October 2026.
[GD25Q16B-xgpro-original.bin](GD25Q16B-xgpro-original.bin) is byte-identical to the
supplied file, without editing, trimming or anonymization.
[SHA256SUMS](SHA256SUMS) · [analysis.json](analysis.json).
This unit-specific file may contain its configuration; publication is an explicit
exception to the usual exclusion of full dumps.

[Chip PDF](../../../docs/datasheets/GD25Q16B_Datasheet_2.3.pdf),
[pinout and page guide](../../../docs/datasheets/README.md#u6-gd25q16bsig).
[Official update packages](../../../vendor/tp-link/tl-sg1218mpe-v5/README.md)
are different from a full flash export.

## Byte-level findings

- Total size **2,097,424 bytes**; first **2,097,152 bytes** form the 2 MiB array.
- A **272-byte** trailer starts with ASCII `-Configuration-` at `0x200000`.
  It is presumed Xgpro export metadata; fields are not decoded. It is retained,
  not treated as additional SPI addresses.
- The complete 1,013,324-byte official 20230616 update image appears at both
  `0x8000` and `0x100000`. SHA-256
  `c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`;
  both CRC32 values are `d31a20a5` and match their headers.
- MIPS32 BE boot code precedes the first copy. Strings: check runtime img at
  `0x6188`, Image recover done at `0x61e4`.

Offsets start at the saved file's beginning; range ends are excluded.

## Initial bootloader analysis

Startup `0x61c..0x654` copies `[0xca0,0x1a00)` to RAM
`[0xbf0025a8,0xbf003308)`. Disassemble those functions using RAM addresses,
not one flash base for the whole file.

`0x18d4..0x1928` reads staging header at `0xb4100000`, checks length/flag bit 0,
calls CRC with `a1=0xb4100010`, `a2=0xf6ff0`, and compares the first header word.
Branches `0x1944..0x1954` and `0x1970..0x1980` pass source `0xb4100000` and
destination `0xb4008000` to the copier.

This supports staging application/recovery behavior, not manual selection of two
firmwares. Later [offline path tests](../../../docs/FINAL-CHECK.md) and
[hardware boot evidence](../../../docs/evidence/2026-10-17-switchlens/README.md)
strengthen that specific path. They do not establish all checks or UART/TFTP
recovery commands.

## Backup/recovery status

One file was supplied. The owner reported programmer verification and resoldering,
after which stock web worked. No second independent file was supplied; two
runtime copies inside one export do not replace independent reads.

Stock UART TX was established at pin 1, R41/R42 0 Ω 0402, 38400 8N1.
Later v0.1.1 help established input/output. Separate UID/OTP/status-register
capture and successful restoration by writing this export remain unverified.
Reading/verification does not establish recovery. The owner declined another
desoldering exercise as a preliminary test. Do not blindly write the export as
raw flash: it has a trailer and loading behavior depends on the programmer.
