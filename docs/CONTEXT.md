**English** | [Русский](CONTEXT.ru.md)

# SwitchLens continuation context

**New v0.1.3:** public `/stats.json`, manual `cool low/fast/auto` without a timer, and `cooling.speed_mode`. Built and emulation-checked; hardware installation pending. [BIN](../releases/v0.1.3-public-stats/README.md). Owner explicitly requested public statistics, permanent low/fast/auto commands and removal of the test commands/time limit.

**Current result:** the problematic fan was replaced with a stock fan; both now rotate and `cool test 0` accelerates both. Earlier no-effect/stopped-fan statements below describe prior tests. [Updated observations and next action](evidence/2026-10-17-cooling/README.md).

Updated **17 October 2026 after the v0.1.2 GPIO27 test and code follow-up**.
This is the entry point for a new chat; read current `main` before continuing.

## Goal and current state

Read-only `GET /stats.json` inside the stock TL-SG1218MPE(UN) V5.0 HTTP server,
for later Prometheus/Grafana collection. SNMP is outside current scope.
No exporter/dashboard has been created yet.

**Working firmware:** web installation, runtime boot, bidirectional UART help
and two valid changing JSON replies are hardware verified on the owner's unit.
[JSON reference](JSON-API.md) · [Messages, screenshots and full samples](evidence/2026-10-17-switchlens/README.md).
Do not repeat obsolete claims that modified firmware has never booted, UART is
output-only or JSON only exists in the emulator.

## Completed sequence

1. Original SPI export, official V5 firmware packages and datasheets archived.
2. Stock UART boot obtained: R41/R42 0 Ω 0402, 38400 8N1.
3. Stock CLI dispatcher found disabled in code. Enter silence did not diagnose RX soldering.
4. v0.1.1 package built: v0.1.0 JSON payload, two CLI instructions, updated CRC.
   Offline review: 20 MIPS tests, host tests, ASan/UBSan. [Report](FINAL-CHECK.md).
5. Owner performed stock web upgrade. Image recover done, runtime entry,
   SignCheck Pass, RTK# and completed code init observed.
6. Owner typed help and received the command list: UART input and output work.
7. Two full JSON responses validated, each with ports 1–18 and changing counters/raw uptime.

## Exact package identity

[GitHub Release](https://github.com/adsdevdoo/switchlens-sg1218/releases/tag/v0.1.1-experimental-uart).
Path: `releases/v0.1.1-experimental-uart/SwitchLens-SG1218MPE-V5-v0.1.1-experimental-uart.bin`.
Size **1,013,324 bytes**; SHA-256:

```text
27e4fce8d5c0c2999a324341cea7e96e37b1c0561e8d6a3218705b32b7aeee71
```

Official base: `1.0.0 Build 20230616 Rel.57668`, SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
Internal version strings and historical artifact names remain unchanged.
The stock version string does not prove rollback. No installed-flash readback
hash was supplied. Do not change BINs or frozen test assets to update their status.

## Bench

One owner's switch, not yet in production. External/UI version V5.0; board label
Ver:5.40, PCB 2060500612. Visible RTL8214FC does not identify the main SoC.
U6 is GD25Q16BSIG, 16 Mbit / 2 MiB.

| Item | Status |
| --- | --- |
| R41/R42 | Both 0 Ω 0402, owner-reported continuity/population |
| J2 pin 1 | Switch TX → adapter RXD |
| J2 pin 2 | RX in described wiring; help proves two-way exchange; no new wiring photo |
| J2 pin 3 | Owner-checked GND |
| J2 pin 4 | Owner-measured 3.3 V; not connected to adapter power |
| UART | CP2102, COM3, 38400, 8N1, Flow None |

Numbers follow the owner's measurement convention, not universal photograph
orientation. “Set adapter to 3.3” is a setting report, not an independent TXD
measurement. [Bench guide](LAB.md), [UART analysis](../research/UART-CONSOLE.md).

## Real observations

[Sample 1](evidence/2026-10-17-switchlens/stats-01.json),
[sample 2](evidence/2026-10-17-switchlens/stats-02.json),
[comparison](evidence/2026-10-17-switchlens/validation-results.json).
Port 1 is up, 1000 Mbps/full; 2–18 are down.
RX bytes 43,610 → 528,836; TX bytes 51,604 → 103,534.
Raw uptime 84 → 614, without exact request timing.
PoE budget 250 W, consumption 0 W, all PoE statuses OFF.
Bridge discards 163 → 3870; cause unconfirmed.

Uptime seconds, general RX discards, TX 256–511 bucket, lag ID, measurement
validity and several flags intentionally remain null. Two changing replies
prove dynamic output, not all metric semantics, read-side effects or stability.

## Recovery and owner decision

Original export: `backups/original/2026-10-17/GD25Q16B-xgpro-original.bin`,
2,097,424 bytes: first 2,097,152 bytes SPI array, then 272-byte Xgpro trailer.
SHA-256 `b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87`.
Both runtime copies match the official update image; they are not independent reads.
Owner used T56/Xgpro to read/verify the chip, then resoldered it.

**Owner declined another desoldering exercise as a preliminary recovery test.**
Do not reintroduce it as a mandatory step. Restoration by writing the dump,
separate UID/OTP/status data and UART/TFTP recovery are unverified. Runtime RTK#
does not establish a bootloader emergency console.

## Current priority: cooling code and GPIO26 monitoring

Prepared [v0.1.2 BIN](../releases/v0.1.2-cooling/README.md): `cool status`, `cool test 0`,
`cool test 1`, `cool auto`; 100 raw-tick hold and return to stock hysteresis.
24 MIPS tests pass; the owner has confirmed this build's CLI and an active GPIO27=0 test.
`/stats.json` adds read-only `cooling`; RPM/health remain null.
[Implementation, commands and limits](COOLING-CONTROL.md).

Owner uses Noctua NF-A4x20 PWM 12 V with three standard wires connected.
The same fan fails to start on either header but runs after a push.
Direction `0x39000000`, data `0x39780000`, orange FAN; one fan runs, one does not.
Manual data change to `0x31780000` and back produced a tentative report of one
fan slowing; the other did not start. Level-to-speed mapping is not established.
Truncated `reg flashget 0x1` hung the old console; the new wrapper validates arguments.
Owner declined measurements and authorized software testing. Do not repeat multimeter
requests or already completed reads as prerequisites. An active `cool test 0;cool status`
showed GPIO27=0 and 100 remaining ticks; separate auto output showed GPIO27=1.
The owner reported no clear fan improvement. v0.1.2 JSON hardware output is pending.
[Further analysis](../research/COOLING-PATHS.md) identifies the PoE bus and confirms
in 32 synthetic combined-poll cases that GPIO26 changes LEDs but not the output
policy. No additional fan-speed command was found in the reviewed paths. Explain
GPIO26 raw-state history, indicator modes and possible aggregate alarms; do not
claim RPM, per-fan health or a proven fault polarity.

## Continue with

[Expanded GPIO audit](../research/GPIO-INVENTORY.md): the previous 23 direct
writer references were not a full GPIO audit. Additional GPIO19/20 paths select
copper/fiber; GPIO21 is used for configuration reset. The RTL8231-named driver
has a constructed data-writer callback in optical-module handling. Stock board
ID 0x43, selected by PHY c984, takes the internal-GPIO media poll instead.
Default generic input/masked-write features are disabled. All 32 snapshot bits
are documented, but physical pin mapping and every computed path remain open.
No additional fan-speed command was identified. Do not claim the external writer
is unused merely because it has no direct callers. Released BINs are unchanged.

[Boot/timer/vendor follow-up](../research/COOLING-FOLLOWUP.md): boot setup sets
GPIO24 and preserves GPIO27; the timer ISR updates counters/flags without GPIO
access. 100 fast IRQ calls produce 5 raw uptime increments (no wall-clock
calibration). The identified GPIO27 controller behaves identically in all four
archived vendor builds: 80 emulator cases pass. No additional speed command was
identified in these paths.

[Web evidence and next step](../research/COOLING-WEB-EVIDENCE.md): the Spot on Tech
replacement photograph shows NF-A4x20 FLX, not PWM; it does not establish our
board revision or pinout. The owner supplied a close-up with NCE9435A, but its
GPIO/fan connection is unknown. They declined further disassembly for now.
The approximately 150 W threshold may enable a second fan; this remains a
hypothesis despite confirmed GPIO27=0 readback. Clarify the ambiguous phrase
“тот что не меняли” before assuming both installed fans are Noctua. Next useful
read-only observation: two cool status outputs with a measured elapsed interval
to calibrate the 100-raw-tick hold. No new BIN or arbitrary GPIO changes.

1. Real PoE consumer and comparison with the stock PoE page.
2. Settings/counters, physical port mapping and discard investigation.
3. Raw uptime calibration against external time.
4. Sustained polling, slow/disconnected clients, counter reset/wrap and long load.
5. Collection integration based on verified fields; deployment decided separately.

## Repository workflow

Owner requests GitHub-plugin publication, not downloadable archives for manual
upload. They authorized detailed documentation and this session's messages/images,
then requested English-first/Russian-switch documentation and working status.
[Contribution rules](../CONTRIBUTING.md) record the scope. Future logs/secrets
are not automatically authorized.

Vendor originals: `vendor/tp-link/`, `docs/datasheets/`; original export:
`backups/original/`; stock logs: `docs/evidence/2026-10-17/`; successful test:
`docs/evidence/2026-10-17-switchlens/`. Historical reports/frozen assets describe
their own dates. Current status is here, in README and [roadmap](ROADMAP.md).
