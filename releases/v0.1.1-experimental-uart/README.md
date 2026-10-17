**English** | [Русский](README.ru.md)

# SwitchLens 0.1.1 — working JSON and UART firmware

Update BIN for **TP-Link TL-SG1218MPE(UN) V5.0**, combining the v0.1.0 JSON
payload with the enabled stock `RTK#` runtime console.

**Hardware verified, 17 October 2026:** stock web upgrade, runtime boot, UART
RTK#/help and two valid `/stats.json` replies with changing counters.
[Owner messages, eight screenshots and full JSON](../../docs/evidence/2026-10-17-switchlens/README.md)
· [JSON reference](../../docs/JSON-API.md).
Loaded PoE, extended stability and recovery remain outstanding.

- [Firmware BIN](SwitchLens-SG1218MPE-V5-v0.1.1-experimental-uart.bin)
- [SHA256SUMS](SHA256SUMS) · [Build manifest](build-manifest.json)
- [6 UART tests](uart-test-results.json) · [10 HTTP/JSON tests](target-test-results.json)
- [Final offline review](../../docs/FINAL-CHECK.md), including [4 additional tests](release-path-test-results.json)
- [Original frozen review artifact](FINAL-CHECK.md)

The historical `experimental-uart` tag/filename is retained to preserve existing
links, hashes and artifacts. Current status: **working firmware with verified
boot, UART and JSON**. BIN and frozen test records are unchanged; their original
pre-hardware status describes the publication moment, not today's test outcome.

## Changes

Based on official `1.0.0 Build 20230616 Rel.57668`. The JSON machine payload is
identical to v0.1.0; the packaging script reproduces that release byte-for-byte
before enabling CLI. Internal version strings remain unchanged.

| Update-BIN offset | Before → after | Purpose |
| --- | --- | --- |
| `0x25e94` | `8c45f018` → `24051fff` | Initialize all 13 stock CLI permission bits to 1 |
| `0x25ed8` | `30420001` → `24020001` | Enable periodic UART-handler invocation |
| `0x0` | `5e9ceeca` → `5c6abcf2` | CRC32 for `[0x10, 0xf7000)` |

The bootloader, HTTP authentication and parameter word at `0xf7018` are unchanged.
[Why stock Enter was silent](../../research/UART-CONSOLE.md).
This is the main-firmware console, not an emergency bootloader menu. Stock commands
include settings/register changes and resets; the CLI is not read-only. The JSON
reader is read-only. Commands beyond help and CLI-based recovery were not tested.

## Validation

Unicorn executed the stock dispatcher, parser and help with low-level UART
replaced by a byte queue. RTK#, CR/LF/CRLF, help, ?, unknown-command and no-input
behavior were checked. The stock image skips Enter without printing a prompt.
All ten HTTP/JSON tests passed with synthetic socket/MMIO, including session,
send failures, stack and CRC. Four further tests cover scheduler invocation,
shared UART/HTTP RAM and accepted/rejected boot-staging paths.

Later the owner's Ver:5.40 board completed web installation, help and two JSON
requests. This establishes initial operation of both interfaces, not electrical
level measurements or a stress test with real interrupts and sustained load.

Size: **1,013,324 bytes**. SHA-256:

```text
27e4fce8d5c0c2999a324341cea7e96e37b1c0561e8d6a3218705b32b7aeee71
```

```powershell
Get-FileHash .\SwitchLens-SG1218MPE-V5-v0.1.1-experimental-uart.bin -Algorithm SHA256
```

## Reproduction

From the repository root with `requirements-dev.txt` installed:

```bash
python3 tools/build_uart_diagnostic.py
python3 tests/test_uart_console.py
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-uart-diagnostic
python3 tests/test_release_paths.py
```

For source compilation, `tools/build_firmware.py --uart-cli` enables the console;
without that option it retains stock CLI-off behavior. [Toolchain and implementation](../../docs/FIRMWARE.md).
These scripts create local files; they do not flash hardware.

## Next checks

Web installation and first boot are complete. Compare values against stock UI,
test real PoE loads and sustained polling. The original SPI export is saved, but
programmer restoration is untested. The owner declined repeat desoldering as a
preliminary prerequisite. If runtime does not boot, web rollback may be unavailable.
An update BIN is not a complete 2 MiB flash dump. Preserve errors if the stock
upgrade rejects an image; do not blindly change bootloader checks.

UART: **38400, 8N1, Flow None**. Pin 1 TX is confirmed; pin 2 RX follows the owner's
described wiring with successful help exchange, without a new wiring photograph.
Pressing Enter alone does not enable the original stock firmware's disabled CLI.
