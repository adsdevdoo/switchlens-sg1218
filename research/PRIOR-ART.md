**English** | [Русский](PRIOR-ART.ru.md)

# Related firmware projects

Primary sources were searched/read on 16 October 2026. “Verified” here means
verified content of an author's publication, not our testing of their hardware.
No ready-made TL-SG1218MPE V5.0 stats.json implementation was found in that limited
search; this is not proof none existed. SwitchLens has since reached its own
[working hardware test](../docs/evidence/2026-10-17-switchlens/README.md).

| Project | Published evidence | Applicability |
| --- | --- | --- |
| [TL-SG108E-V5-custom-firmware](https://github.com/YurkoWasHere/TL-SG108E-V5-custom-firmware) | Author reports flashing/testing a MAC-table page on one SG108E 5.0; builder pins original hash; BINs excluded | Example of extending stock Easy Smart telemetry, not a compatible image |
| [Realtek_switch_hacking: SG116M](https://github.com/libc0607/Realtek_switch_hacking/blob/master/SG116M-RE-Boot.md?plain=1) | Big-endian MIPS RTL8382L startup, vectors/data/zeroing/code copy, initial SP BF01F800 | Startup sequence/SP match our static analysis; not board identification |
| [RTLPlayground](https://github.com/logicog/RTLPlayground) | RTL8372/RTL8373 firmware sources with HTTP/upgrade/statistics, SDCC/mcs51 build | Compact web-management example, not a MIPS image to port directly |

The [SG108E technical notes](https://github.com/YurkoWasHere/TL-SG108E-V5-custom-firmware/blob/main/REVERSE_ENGINEERING.md)
use banked 8051, a 20-byte header and byte sums. Our image is MIPS, 16-byte header,
CRC32. Addresses, machine code and packaging do not transfer directly. Bounded
stock-buffer output and branch tests are useful methodology. The author's single
unit test does not establish recovery or long-duration stability. No external
project code was copied into SwitchLens.

The selected approach was one stock HTTP dispatcher extension, RAM/ASIC reads and
streaming system/ports/PoE JSON. No flash-stored JSON, replacement network stack
or complete firmware rewrite was necessary. That approach is now implemented.

## Timer source

[Linux timer-rtl-otto.c](https://github.com/torvalds/linux/blob/master/drivers/clocksource/timer-rtl-otto.c)
describes matching DATA/CTRL/INT, divisor and periodic-mode behavior. Its LXB
200 MHz comment for non-RTL930x platforms is not a measurement of this unit's
clock. Conditional calculation: [platform follow-up](PLATFORM-FOLLOWUP.md).

## Reproducibility

Queries included the exact model with custom firmware, the SG108E project name
and Realtek RTL8382L firmware. External projects were not executed/flashed.
Mutable main/master URLs refer to the state read on that date; source-text hashes
are in [prior-art-source-hashes.json](prior-art-source-hashes.json), not signed
release hashes.

## Additional UART source — 17 October

An [OpenWrt SG2210P commit](https://lists.infradead.org/pipermail/lede-commits/2022-September/015377.html)
describes missing R27/R28, 0–50 Ω installation and BOOTUTIL at 38400. This is a
different model; designators, packages and commands are not transferable.
Our owner's independent board evidence establishes R41/R42 **0 Ω 0402**, J2 pin 1
TX and **38400 8N1**; [stock log](../docs/evidence/2026-10-17/boot-stock-38400.txt).
The later own-device help test establishes runtime CLI. Neither source establishes
the factory resistor nominal values or a recovery menu on this model.
