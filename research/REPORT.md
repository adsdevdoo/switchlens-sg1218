**English** | [Русский](REPORT.ru.md)

# Initial firmware analysis — historical findings

Original investigation: 16 October 2026. [Unchanged source record](REPORT.txt).
Later results supersede the original no-build/no-UART/no-dump stage: **v0.1.1 is
working firmware**, with web boot, help and changing JSON observed on hardware.
[Current evidence](../docs/evidence/2026-10-17-switchlens/README.md).

## Object and method

Input `SG1218MPE(UN) 5.0_1.0.0 Build 20230616 Rel.57668_up.bin`, 1,013,324 bytes
(0xf764c), SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
Strings: TL-SG1218MPE 5.0 at 0xd82f4, Jun 16 2023 at 0xd6344.
Initially owner-supplied; later matched to the official ZIP in the vendor archive.
Python 3/zlib/Capstone 5.0.9 and targeted MIPS analysis were used, not Binwalk/Ghidra.
File offsets include the 16-byte header and range ends are excluded.
`tools/audit.py` pins SHA, reads only and does not access a device/network.

## Platform

Big-endian MIPS32, instructions including ext/seb consistent with MIPS32r2.
Flash code uses file offset + BFC08000; entry BFC08010, initialization file410,
main BFC2E760 reached at file6f8. A path at d3094 contains
`realtek_mcu/CPU_RTL838x_RTL833x/EasySmart_V3/.../dal/maple/dal_maple_l2.c`.
Maple/RTL838x is the supported family hypothesis, not exact SoC identification;
word 0x8380 at f7040 alone is insufficient.

Startup copies vectors 10:410 → BF000000; data 720:3164 → BF000400;
zeros BF002E40:BF01952C; copies RAM code 3160:8178 → BF019528:BF01E540;
sets SP BF01F800. Four-byte overlaps come from loop ordering, clarified in
[platform follow-up](PLATFORM-FOLLOWUP.md). Main 26a44:26b74 and direct hardware
initialization suggest compact standalone/event-driven runtime; exact RTOS is
unknown. Absence of Linux/eCos/FreeRTOS strings is not proof. Studied code/web
assets are readable without decompression; other compressed subblocks are not excluded.

## Header and checks

| Offset | Big-endian value | Observed meaning |
| --- | --- | --- |
| 0x00 | d31a20a5 | CRC32 |
| 0x04 | 000f763c | File length minus 16 |
| 0x08 | 0dffffff | First byte checked with mask 5; remaining bit meanings unknown |
| 0x0c | 184d5005 | ID compared by web upgrader |

CRC covers `[0x10,0xf7000)`, not the tail. Web upgrader BFC3DD20 checks
length/ID/flags; file36014:36038 computes CRC for staging+10, length f6ff0.
CRC RAM function BF01B480 corresponds to file50b8.
SignCheck BFC4D718/file45718 is called at file26614 and affects HTTP/TSDP startup
from2664c. It reads UID and 128-byte signature B41FC006:B41FC086 via BFC5141C,
with RSA1 and Pass/Fail. Later analysis confirms SHA-1 input is UID, not the
runtime range; this does not rule out other boot-chain checks.

## Statistics and MIB

Route string `/PortStatisticsRpm.htm` at d5d54; comparison34258:34264;
branch34280 to BFC4163C/file3963c, iterating18 ports. pkts format at d6c60
is `%u,%u,%u,%u,`; web passes only low words of software64 aggregates at39894:398b8.

| Wrapper | File | Sources |
| --- | --- | --- |
| BFC59870 | 51870 | RX selectors2,4,6 |
| BFC59638 | 51638 | RX bad aggregate37,34,43,40,31 |
| BFC59498 | 51498 | TX selectors10,12,14 |
| BFC59390 | 51390 | TX bad selector21 |

MIB API BFC27FB8 → BFC1D930/file15930 takes unit, physical port, selector,
output pointer; status return and high/low output words are reconstructed ABI.
CLI table94170 names rx bytes selector0, tx bytes8, tx drop16, but prints only
low `%lx`, unsuitable as a complete64-bit reader. Jump table93250:
0→BFC1D9E8 and8→BFC1DA30 read both but expose low;1→BFC1DA00 and9→BFC1DA48
expose both;16→BFC1DA8C exposes32-bit drop with high0.

Block base `0x1200+(physical_port<<8)`; RX high/low +0/+4, TX +8/+c, TX drop +2c.
Read BFC10768/file8768 uses MMIO `0xbb000000 | offset` or installed callback.
Two-word code does not establish all64 meaningful hardware bits or coherent wrap.
Mapping BFC55C3C/file4dc3c maps logical16/17→ASIC24/25, leaves0–15 unchanged.
Check panel labels and LAG semantics; stock wrappers may aggregate group members.
RX discards and exact IF-MIB interpretation of TX drops were not established.

## HTTP, UDP and timer

Formatted HTTP BF01CBF8/file6830 uses BF011550 and formatter BFC339DC, then raw
BF01CAC0. Later analysis established the actual1460-byte transport buffer and
hidden error returns: [HTTP follow-up](HTTP-JSON-FOLLOWUP.md). Chosen implementation
streams short fragments and explicitly checks final send, without a new thread
or flash-stored JSON.

TSDP initialization file3fcf0 creates protocol17 via BFC38780, registers callback
BFC48DB0 and binds BFC38B3C to29808. Send to29809 at40828:40844 uses BF01CA4C/file6684,
which checks protocol17 then BF01C7D4. Its full ABI/lower network path is not
established and was not selected for JSON.

ISR BF01A094/file3ccc increments BF002E94; every20 increments BF002E90.
Main polls/clears timer flags through BFC10480/BFC10498 and calls BFC2DF8C.
Raw uptime is usable as raw data, not confirmed seconds. No RTOS-task creation
API was identified.

## Space, recovery and subsequent decisions

`[d8640,f7000)` contains125,376 FF bytes, later used in part for payload.
RAM-code end BF01E540 to initialSP BF01F800 is4800 bytes, not measured free RAM;
stack and interrupts use it. Approximately128KiB SRAM remained a hypothesis.
RTK#/tftp/reset/reboot strings alone did not prove accessible recovery.

The original gate deferred flashing pending image/stack/recovery work. Later
build, emulation and owner-authorized web installation succeeded. The owner
explicitly declined another preliminary desoldering test; recovery remains
unverified rather than a newly imposed mandatory task. Original speculation about
sessionless local JSON was not implemented: stock authentication is retained.
No JSON file is written to flash. Current fields/limits are in the
[API reference](../docs/JSON-API.md), not this historical proposal.
