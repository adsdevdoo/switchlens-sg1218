**English** | [Русский](README.ru.md)

# First successful SwitchLens hardware test

**17 October 2026, owner's bench.** TL-SG1218MPE(UN) V5.0, board label Ver:5.40.
The owner performed hardware actions. We analyzed their messages and attachments;
there was no remote connection from the analysis environment to the switch.

**Result:** the stock web upgrade was followed by a successful runtime boot,
`RTK#` appeared, and `help` returned a command list. `/stats.json` opened in the
browser. Two complete replies validate against the schema and show changing
counters. **The firmware is working on this unit.** Loaded PoE, every metric's
accuracy, recovery and extended operation remain separate outstanding checks.

## Tested package

The session used the published [v0.1.1 package](../../../releases/v0.1.1-experimental-uart/README.md):
`SwitchLens-SG1218MPE-V5-v0.1.1-experimental-uart.bin`, 1,013,324 bytes.

```text
SHA-256 27e4fce8d5c0c2999a324341cea7e96e37b1c0561e8d6a3218705b32b7aeee71
```

[GitHub Release](https://github.com/adsdevdoo/switchlens-sg1218/releases/tag/v0.1.1-experimental-uart).
The historical filename/tag is retained; the current product status is working
firmware. The internal stock `1.0.0 Build 20230616 Rel.57668` string is unchanged.

The pre-selection upgrade screenshot does not show the chosen filename. No
post-install flash readback hash was supplied. Package association follows the
session sequence and the appearance of both added functions. The SHA above is
for the published file, not a hash read back from the installed switch.

## Owner actions and observations

| Action | Supplied evidence | Established result |
| --- | --- | --- |
| Prepared UART and opened PuTTY | Readable stock boot; said the adapter was set to 3.3 | Receive path works; selector position alone is not a TXD measurement |
| Pressed keys before modification | Reported no response | Later analysis found stock CLI disabled; silence did not establish bad soldering |
| Opened System Info and Firmware Upgrade | TL-SG1218MPE, Hardware 5.0, stock build and upgrade form | Stock web access works |
| Started web upgrade | 5% progress, then back up/reboot countdown in UART | Upgrade and reboot initiated |
| Waited for boot | Image erase all, Image recover done, runtime entry, SignCheck Pass, RTK#, code init | Main runtime started and CLI prompt appeared |
| Typed help | Command list and another prompt | UART input/output and command handling work |
| Opened stats.json | Browser image and first full text | Complete 18-port JSON received |
| Repeated/refreshed the request | Second full text | Counters and raw uptime changed |

The order is established from the session; no independent request timestamps
were recorded. A suggested “30 seconds” is not a measured interval. The 530-tick
increase does not establish seconds per tick.

### Before installation: stock UART and web UI

![Stock boot without CLI prompt](01-stock-uart.png)

![System Info before the upgrade](02-system-info.png)

### Stock web upgrade

![Firmware Upgrade before file selection](03-upgrade-form.png)

![Upgrade in progress at 5 percent](04-upgrade-progress.png)

![Reboot countdown and runtime-image check](05-reboot-start.png)

### Modified-runtime boot

![Completed boot with SignCheck Pass and RTK#](06-boot-rtk.png)

[Complete supplied boot text](boot-after-upgrade.txt) is copied from the owner's
message, not a raw UART-byte capture. `Image erase all!` followed by
`Image recover done!` is consistent with the traced staging-to-active-image path;
the words alone are not proof of rollback. Both added functions are observed
afterward. Individual hardware flash writes were not traced in this session.

`SignCheck Pass.` is an observed stock runtime check, not a byte-for-byte
attestation of the entire installed image. Port/PoE initialization messages do
not prove sustained forwarding or operation with a powered device.

### UART help

![Owner typed help and received the stock command list](07-uart-help.png)

[Complete help text](uart-help.txt). The prompt, command input and response are
verified. Other listed commands were not executed in this test; some modify
settings/registers or reset the device. This is the runtime console, not a
confirmed bootloader recovery mechanism.

Current bench: CP2102, COM3, **38400, 8N1, Flow control None**. R41/R42 are
0 Ω 0402. J2 pin 1 TX, pin 2 RX and pin 3 GND follow the owner's numbering and
described wiring; adapter power is not connected to pin 4. No new wiring photo
was supplied. The screenshot proves bidirectional exchange; assigning RX to pin 2
also relies on the described connection.

### First JSON response

![Beginning of the real JSON in the browser](08-stats-json.png)

The screenshot is partial. Validation used the **complete text attachments**:

- [Sample 1](stats-01.json), [original Markdown attachment](stats-01-submitted.md).
- [Sample 2](stats-02.json), [original Markdown attachment](stats-02-submitted.md).
- [Machine validation and all differences](validation-results.json).
- [Complete JSON field reference](../../JSON-API.md).

## Comparison

Both parse as JSON and pass the current [schema](../../../schema/stats.schema.json)
with **zero errors**. Each has ports 1–18 in order, and every decimal counter is
within uint64 range. This checks structure/range, not metric calibration.

| Measurement | First | Second | Change |
| --- | ---: | ---: | ---: |
| `system.uptime_ticks_raw` | 84 | 614 | +530 |
| Port 1 `rx_bytes` | 43,610 | 528,836 | +485,226 |
| Port 1 `tx_bytes` | 51,604 | 103,534 | +51,930 |
| Port 1 `rx_good_packets` | 347 | 4,702 | +4,355 |
| Port 1 `tx_good_packets` | 137 | 435 | +298 |
| Port 1 `rx_bridge_discards` | 163 | 3,870 | +3,707 |

Both show port 1 up at 1000 Mbps/full duplex and other ports down.
`rx_crc_align_errors`, `symbol_errors`, `collisions` and stock bad-packet aggregates
are zero. Additional MIB naming remains provisional; the reason for increasing
bridge discards is unknown.

PoE budget=250 W, consumption=0 W, remaining=250 W. Ports 1–16 are enabled in
configuration but report OFF, with null per-port measurements. Ports 17–18 have
`poe: null`. This is consistent output, not a loaded-PD test. Config speed codes
are 5 for ports 1–5, 2 for 6–16, and 1 for 17–18, unchanged between replies;
comparison against Port Setting is pending. Config code is not actual speed.

## Verification boundary

| Check | Status |
| --- | --- |
| Stock web upgrade and runtime boot | Confirmed by the supplied sequence |
| RTK#, help, bidirectional UART | Confirmed on owner's unit |
| JSON availability, 18 ports, valid structure | Confirmed in two complete responses |
| Changing uptime/counters | Confirmed by file comparison |
| Installed flash identical to published BIN | No post-install readback supplied |
| All values versus stock UI / known traffic | Pending |
| PoE load, PD classes, voltage/current/power | Pending |
| Discard cause, counter wrap/reset and read side effects | Pending |
| Uptime time unit and sustained polling interval | Unconfirmed |
| Long load, multiple clients, HTTP failures | Not hardware-tested |
| Rollback/recovery | Untested; owner declined repeat desoldering as a preliminary test |

## Provenance and publication

The owner explicitly requested a detailed JSON description and publication of
successful results with their messages and screenshots; subsequently requested
English/Russian documentation and working-firmware status. This authorizes the
current session's real network values, messages and images. Selected materials
contain no passwords or session cookies.

[Messages with context](messages.md) are a relevant selection, not a complete
chat transcript. Screenshots and original Markdown attachments are byte-identical
to uploads. Extracted JSON only removes Markdown fences and outer whitespace.
[sources.json](sources.json) records original names, transformations and SHA-256.
[SHA256SUMS](SHA256SUMS) covers this directory except itself.

This authorization does not cover future sessions automatically. Firmware BINs,
original SPI export and frozen pre-hardware verification artifacts are unchanged.
Their old statuses refer to the time before this test; this document provides
the later hardware observations.
