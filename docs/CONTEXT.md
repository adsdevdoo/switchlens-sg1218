**English** | [Русский](CONTEXT.ru.md)

# SwitchLens continuation context

Updated **17 October 2026 after the first successful v0.1.1 hardware test**.
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

## Continue with

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
