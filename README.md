**English** | [Русский](README.ru.md)

# SwitchLens

Working firmware for the **TP-Link TL-SG1218MPE(UN) V5.0**, adding read-only JSON
telemetry and the stock UART command console.

**Hardware verified on 17 October 2026:** the owner installed v0.1.1 through the
stock web interface, booted the switch, ran UART `help`, and retrieved two valid
`/stats.json` responses with changing counters. The tested unit has PCB label
**Ver:5.40**, PCB **2060500612**, and reports hardware version **5.0** in the UI.

- **[JSON API reference: every field, units, codes and null values](docs/JSON-API.md)**
- **[Successful hardware test: owner messages, eight screenshots, logs and JSON](docs/evidence/2026-10-17-switchlens/README.md)**
- **[Download v0.1.1](https://github.com/adsdevdoo/switchlens-sg1218/releases/tag/v0.1.1-experimental-uart)** · [Release notes](releases/v0.1.1-experimental-uart/README.md)
- [Documentation index](docs/README.md) · [Continue in a new chat](docs/CONTEXT.md)

The historical `experimental-uart` suffix remains in the existing tag and filename
so that download links, hashes and archived artifacts remain valid. The current
status is **working firmware with hardware-verified boot, UART and JSON**.
Loaded PoE operation, all counter semantics, recovery and long-duration operation
are separate outstanding checks. See [roadmap](docs/ROADMAP.md).

**v0.1.2 console and GPIO27 test confirmed on hardware.** [BIN and checks](releases/v0.1.2-cooling/README.md), [`cool` commands](docs/COOLING-CONTROL.md). Active level-0 readback and automatic mode were observed; no clear fan improvement was reported. [Further code analysis and GPIO26 options](research/COOLING-PATHS.md). v0.1.2 JSON hardware verification remains pending.

## Current firmware

File: `SwitchLens-SG1218MPE-V5-v0.1.1-experimental-uart.bin`, **1,013,324 bytes**.

```text
SHA-256 27e4fce8d5c0c2999a324341cea7e96e37b1c0561e8d6a3218705b32b7aeee71
```

The base is TP-Link `1.0.0 Build 20230616 Rel.57668`. Its internal version string
is intentionally unchanged. v0.1.1 uses the same JSON payload as v0.1.0 and adds
two UART-enabling instructions plus a recalculated CRC. The bootloader, existing
HTTP authentication and the parameter word outside the CRC region are unchanged.
The UART console includes stock configuration/reset commands; `/stats.json`
itself only reads telemetry.

The earlier [v0.1.0 package](releases/v0.1.0-experimental/README.md) is retained
for reproducibility. Its SHA-256 is
`58d48cf69cac4024eddfb4ede1bb5a925420521a0f0e44011ff4fa08940c2e25`;
it was not independently tested on hardware. Hardware observations concern v0.1.1.

## What the JSON provides

Log in to the stock web interface and open `http://<switch-address>/stats.json`
in the same browser. The existing session is required.

- System description, MAC, IPv4, subnet, gateway, hardware/software strings.
- Status and settings of 18 ports, including link speed and duplex.
- A fixed structure of 49 counter fields per port, including byte totals,
  packet categories, errors/discards and size categories.
- Global PoE budget/consumption/remaining power, per-port status and measurements,
  priority, power limits and Auto Recovery configuration/statistics.
- Raw uptime and loop-prevention masks; unconfirmed values remain `null`.

Counter values use decimal strings to preserve integer precision. Many underlying
counters are 32-bit; a JSON string does not make them hardware 64-bit counters.
Additional MIB names are based on a statically matched RTL838x register map;
their precise semantics remain subject to device testing. They are not asserted
to be IF-MIB equivalents. `uptime_seconds`, `rx_discards` and
`tx_packets_256_511` intentionally remain `null`.

The handler streams data through the stock HTTP server, without a new task, heap
allocation or a stored JSON file in flash. See [implementation](docs/FIRMWARE.md).
[Demo data](examples/demo.synthetic.json) is synthetic; the separately labelled
[hardware samples](docs/evidence/2026-10-17-switchlens/README.md) are real.
Prometheus collection and Grafana dashboards are the next integration goal;
an exporter/dashboard is not included yet. SNMP is outside the current scope.

## Successful hardware test

![UART help on the installed firmware](docs/evidence/2026-10-17-switchlens/07-uart-help.png)

![First real stats.json response in the browser](docs/evidence/2026-10-17-switchlens/08-stats-json.png)

Both full JSON responses pass the schema and contain ports 1–18. Port 1 reports
1000 Mbps/full duplex. RX bytes changed from 43,610 to 528,836; TX bytes from
51,604 to 103,534; raw uptime from 84 to 614. Exact elapsed capture time was not
measured. PoE reports 0 W used from a 250 W budget. `rx_bridge_discards` increased
from 163 to 3,870; the cause has not been established.

[The complete chronology](docs/evidence/2026-10-17-switchlens/README.md) includes
System Info, the upgrade form/progress, reboot and runtime logs, `RTK#`, `help`,
the browser screenshot, both complete JSON attachments and machine validation.
No flash readback hash was provided after installation; the package association
comes from the documented session and appearance of both added features.

## Board and UART

![Board overview and Ver:5.40 label](docs/images/board-overview.png)

![RTL8214FC marking](docs/images/rtl8214fc-marking.png)

The visible RTL8214FC marking identifies that chip, not the processor under a
heatsink. RTL838x remains the researched platform family; photographs do not
prove the exact SoC model. Additional original photographs:
[close-up](docs/images/chip-detail.png), [header backside](docs/images/header-backside.png).
The successful test on this unit does not establish compatibility with every
board carrying the same label.

### UART on the owner's bench

| Item | Observed status |
| --- | --- |
| R41/R42 | Both populated with **0 Ω, 0402**; continuity and modification confirmed by owner; factory schematic value unknown |
| J2 pin 1 | Switch TX → USB-UART RXD; readable output confirmed |
| J2 pin 2 | Switch RX in the owner's described wiring; `help` proves bidirectional communication; no new wiring photo |
| J2 pin 3 | GND according to owner's checks |
| J2 pin 4 | 3.3 V according to owner's measurement; do not connect adapter power here |
| Serial settings | **38400 baud, 8N1, Flow control None**, CP2102, COM3 on this PC |
| Verified | Stock boot output, v0.1.1 boot, RTK# and response to help |
| Outstanding | Other CLI commands, recovery, loaded PoE and long-duration testing |

Pin numbers follow the owner's measurement convention. Do not infer numbering
from the top/bottom of a photograph or assume it applies to another board.
For bidirectional operation connect common ground, switch TX to adapter RXD,
and switch RX to compatible-level adapter TXD. Adapter VCC/5V/3V3 remain
unconnected. Soldering or rewiring is performed with switch power and USB-UART
disconnected. For receive-only capture, leave adapter TXD unconnected.

![J2 and R41/R42 before population](docs/images/uart/j2-before-mod.jpeg)

This photograph predates resistor installation; component value/package and the
successful modification were reported by the owner. Verify traces on a different
board before assuming empty resistor positions serve the same purpose.

The original firmware contains the CLI code but disables its dispatcher. Silence
after Enter on stock firmware was not a solder-joint test. [Code evidence](research/UART-CONSOLE.md).
`RTK#` is the runtime console, not a confirmed bootloader recovery menu.

### Capture and original evidence

Close PuTTY before running the receive-only capture script from the repository:

```powershell
.\tools\start-uart.cmd -Port COM3 -Baud 38400 -OutputDirectory "$PWD\uart-logs"
```

After `LISTENING`, power up the bench. Default capture length is 60 seconds;
outputs are `rx.bin`, `rx.txt`, `rx.hex.txt`, `session.json`.
[Full instructions](docs/UART-CAPTURE.md).

[Original stock boot text](docs/evidence/2026-10-17/boot-stock-38400.txt) is the
owner's complete pasted message, not raw UART bytes. Its `SignCheck Pass.` refers
to the stock session; the later modified-runtime observation is archived separately.
The `phy is 0xc984` line does not establish an exact SoC model; firmware port
numbers 24–27 do not by themselves establish front-panel mapping. `POE init`
is not a loaded-PoE test.

![Readable stock boot output](docs/images/uart/putty-boot-38400.png)

Earlier diagnosis is retained in the [stock evidence journal](docs/evidence/2026-10-17/README.md):
[COM3 loopback](docs/images/uart/loopback-com3.png),
[path error](docs/images/uart/capture-path-error.png),
[pin 1 no data](docs/images/uart/pin1-no-data.png),
[repeat pin 1](docs/images/uart/pin1-no-data-repeat.png),
[pin 2 no data](docs/images/uart/pin2-no-data.png),
[unreadable output](docs/images/uart/putty-unreadable.png),
[old serial settings](docs/images/uart/putty-serial-initial.png).
The 115200 settings in those old images are historical; the working rate is 38400.
Original filenames and hashes: [image provenance](docs/images/sources.json).

## Build and local verification

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
make test
./build/fixture > demo.synthetic.json
ASAN_OPTIONS=detect_leaks=0 make sanitize
python3 tools/generate_fields.py
git diff --exit-code -- include/sg_fields.h src/sg_fields.inc
```

These host checks do not access or flash a switch. They require a C99 compiler,
make and Python. LeakSanitizer was disabled in the preparation environment;
AddressSanitizer and UndefinedBehaviorSanitizer remained enabled.
The firmware additionally passed 6 UART, 10 HTTP/JSON and 4 scheduler/boot-path
MIPS tests. [Final offline review](docs/FINAL-CHECK.md) explains their limits.

The builder accepts only the original 20230616 update BIN with SHA-256:

```text
c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32
```

[Vendor files](vendor/tp-link/tl-sg1218mpe-v5/README.md) include all four V5 builds.
Auditors verify this input hash before analysis:

```bash
python3 tools/audit.py /path/to/firmware.bin
python3 tools/audit_mib.py /path/to/firmware.bin > local-mib-map.json
python3 tools/audit_platform.py /path/to/firmware.bin > local-platform-evidence.json
```

Runtime SignCheck hashes the flash UID; this is not a claim that no other image
checks exist. The RAM-code end to initial-SP distance is 4800 bytes, not guaranteed
free stack. [Platform analysis](research/PLATFORM-FOLLOWUP.md).
[Related projects](research/PRIOR-ART.md) inform the method, not binary compatibility.

## Repository layout

| Directory | Contents |
| --- | --- |
| `src/`, `include/` | Streaming JSON and MIB reader |
| `target/` | MIPS route, firmware adapter and linker script |
| `tests/` | Synthetic sources, transport and boundary checks |
| `schema/`, `examples/` | JSON contract and synthetic examples |
| `tools/` | Field generation, audits and local BIN builds |
| `research/` | Findings, offsets, source maps and historical analysis |
| `docs/` | English/Russian guides, status and evidence |
| `releases/` | Versioned BINs, checksums and build records |
| `vendor/tp-link/tl-sg1218mpe-v5/` | Original vendor ZIP/BIN/PDF packages |
| `backups/original/2026-10-17/` | Unmodified original SPI export and analysis |
| `docs/datasheets/` | Original GigaDevice/Realtek PDFs and provenance |

The owner explicitly authorized publication of the original SPI export, board
photographs, stock UART evidence and this successful test session, including its
IP/MAC data. Future logs and credentials are not published automatically.
[Contribution and evidence rules](CONTRIBUTING.md).

The next checks are real PoE loads, comparison with stock UI, port mapping,
discard behavior, uptime calibration and sustained polling. Recovery remains
untested; the owner declined another desoldering exercise as a prerequisite.
The unit is not yet in production. Deployment is a separate decision.

SwitchLens is independent of TP-Link. A source-code license has not yet been
selected. Vendor firmware and datasheets retain their owners' rights; original
notices remain intact. [GitHub workflow](docs/GITHUB.md) ·
[Flash pinout](docs/datasheets/README.md#u6-gd25q16bsig).
