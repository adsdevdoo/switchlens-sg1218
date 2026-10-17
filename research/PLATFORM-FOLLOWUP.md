**English** | [Русский](PLATFORM-FOLLOWUP.ru.md)

# Timer, memory and firmware checks

Static investigation dated **16 October 2026**, targeting SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
“Verified” in this analysis means instructions/bytes inspected, not a hardware
measurement. Ranges are half-open and file offsets include the update header.

**Later status:** the original flash was identified/exported, the patch built,
and v0.1.1 web boot/UART/JSON were observed. [Current evidence](../docs/evidence/2026-10-17-switchlens/README.md).
Original no-build/no-dump assumptions are historical; recovery and maximum IRQ
stack use remain unresolved.

| Question | Static finding |
| --- | --- |
| Image signing | Located runtime SignCheck hashes UID; this does not exclude other bootloader image checks |
| Code space | 125,376 FF bytes inside CRC coverage; later payload placement/build checks use part of this region |
| RAM headroom | 4,800 bytes from RAM-code end to initial SP, not measured free stack; a stock frame uses 3,584 bytes |
| Uptime scale | Divisor 10,000, period 1,000, software divider 20; one second per raw tick only if LXB is 200 MHz |
| Hardware status | Initial planning lacked boot/recovery proof; later initial boot works, recovery is still untested |

## Runtime SignCheck

Function `BFC4D718`, file `0x45718`:

1. `0x45778` calls `BFC1044C` with a0=sp+0x18. Getter `0x844c..0x8480`
   copies from `BF016A9C`, length `word[BF002E80]`.
2. The same length is stored at sp+0x500 (`0x457b0`, `0x457c8`).
3. `0x46038..0x46090` creates SHA-1 context. `BF01E1C8` receives
   a1=sp+0x18 and a2=word[sp+0x500]: UID buffer, not the update-image range.
4. The 128-byte signature comes from `[B41FC006,B41FC086)` through
   `BFC5141C`, file `0x4941c..0x49450`; RSA/PKCS#1/SHA-1 comparison is discussed
   in [HTTP follow-up](HTTP-JSON-FOLLOWUP.md).

A device-binding purpose is an inference, not manufacturer documentation. There
is no reason in this patch to bypass it. This finding does not rule out an
additional image signature check earlier in boot.

## Web upgrade and staging

File `0x35d20..0x36164` writes the image to `B4100000`. CRC is computed over
staging+0x10 for `0xf6ff0` bytes and compared with the first word
(`0x36014..0x3603c`). On success it writes 16 zero bytes to `B4008000`
(`0x36040..0x36068`) and stores 7 at `BF0013E0`. Handler
`0x30048..0x300e0` decrements the countdown, prints reboot at zero and calls
`BFC280A0` → `BFC1F564` (file `0x17564`).

Initially, copying staging to the active image was a hypothesis because the update
BIN omitted the bootloader. The later full export and [offline path review](../docs/FINAL-CHECK.md)
trace a specific header/CRC/copy/handoff branch. The [hardware sequence](../docs/evidence/2026-10-17-switchlens/README.md)
also reaches runtime. This does not establish all recovery paths. B4 addresses
are virtual mappings, not programmer offsets.

## RAM and stack

Startup `0x620..0x708`, including branch-delay behavior:

| Operation | File source | RAM destination |
| --- | --- | --- |
| Vectors | `[0x10,0x410)` | `[BF000000,BF000400)` |
| Initial data | `[0x720,0x3164)` | `[BF000400,BF002E44)` |
| Zero fill | — | `[BF002E40,BF01952C)` |
| RAM code | `[0x3160,0x8178)` | `[BF019528,BF01E540)` |
| Initial stack | — | `SP=BF01F800` |

The 4-byte overlaps follow the loops' compare/store order: final data word is
zeroed, final zeroed word replaced with first code instruction. They are not table
boundary errors. `BF01F800-BF01E540=4800`. Function at `0x4c1dc` allocates
0xe00=3584 bytes; adjacent `0x4c2f4` allocates 3568. They are different functions,
not automatically additive frames. The negative-SP scan in platform-evidence.json
does not replace a call graph and interrupt accounting.

RSA allocator `0x7948..0x7b10`, RAM `BF01DD10`, uses fixed small pools and rejects
sizes over 256 bytes. It is not a general-purpose heap for the new handler.
An approximately 128 KiB SRAM window is a hypothesis; space above initial SP
and peak available stack need separate validation.

The implementation therefore streams without malloc, a full JSON snapshot or
all-port stack array. The serializer buffer is 128 bytes, not total stack usage.

## Timer

`BFC104B0` / `0x84b0`, called with index 0 at `0x86c4..0x86cc`, forms base
`B8003100`, writes `0x01002710` to CTRL +8 and 1000 to DATA +0.
`BFC10504` enables CTRL bit 28 and INT +12 bit 20.
ISR `BF01A094`, file `[0x3ccc,0x3dec)`, increments uint32 at `BF002E94` each call;
every twentieth new value increments uint32 at `BF002E90`. It acknowledges
INT bit 16 at `B800310C`.

The register layout/bits match [Linux timer-rtl-otto.c](https://github.com/torvalds/linux/blob/master/drivers/clocksource/timer-rtl-otto.c):
CTRL low 16 bits are divisor, bit 24 periodic mode. The source describes LXB
200 MHz outside RTL930x. Applicability to this switch's clock is unconfirmed.

```text
Conditional on LXB = 200 MHz:
IRQ interval = 10000 * 1000 / 200000000 = 0.05 s
raw uptime unit = 20 * IRQ interval = 1 s
```

Without confirmed clock/bench calibration, uptime_seconds stays null and raw
uptime stays explicitly uint32. It counts serviced interrupts, not an independent
wall clock; missed/delayed interrupts and wrap need consideration. No timer change
is required. Two later samples show growth, not a measured time scale.

## Reproduce

```bash
python3 tools/audit_platform.py /path/firmware.bin > platform-evidence.local.json
python3 tools/disassemble.py /path/firmware.bin 0x620 0x708
python3 tools/disassemble.py /path/firmware.bin 0x844c 0x8544
python3 tools/disassemble.py /path/firmware.bin 0x45718 0x46238
python3 tools/disassemble.py /path/firmware.bin 0x36014 0x36094
```

The stdlib tool reads local files, rejects wrong SHA and modifies no firmware/device.
Correct input passed; empty, truncated and single-byte-modified inputs were rejected.
SignCheck interpretation also uses manually traced instructions; the tool is not
an automatic proof that no other checks exist. Later build/bench work is recorded
separately in the implementation guide and hardware journal.
