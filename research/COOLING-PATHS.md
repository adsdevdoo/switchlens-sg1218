**English** | [Русский](COOLING-PATHS.ru.md)

# Cooling paths after the GPIO27 hardware test

17 October 2026. The owner reports v0.1.2 running. Its console showed GPIO27
at 0 during an active bounded test and at 1 in a separate automatic-mode
observation. No clear fan-speed change or successful start of the second fan
was reported. Register readback proves the software output bit changed; it
does not prove a particular voltage or speed at either fan header.

This follow-up searches beyond the already identified GPIO27 controller.
The source is the stock June 2023 BIN, SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
Addresses below refer to that image. This work changes documentation and
offline analysis tools, not the released BIN.

## Where the control is

| Routine | Virtual address | File interval | Role |
| --- | --- | --- | --- |
| Output wrapper | `0xbfc5c344` | `0x54344..0x54368` | Writes GPIO27, accepting only 0 or 1 |
| Automatic policy | `0xbfc5c368` | `0x54368..0x543fc` | PoE sum and previous state select the output |
| Input/LED handling | `0xbfc5e0a4` | `0x560a4..0x56184` | Reads GPIO26 and selects LED modes |
| Combined poll | `0xbfc5e2fc` | `0x562fc..0x56338` | Calls budget LED, input LED, then automatic policy |
| PoE initialization | `0xbfc5e994` | `0x56994..0x56a7c` | Sets up GPIO26/27, pulses GPIO24, initializes the bus and devices |

The automatic policy is equivalent to the following for a normal state of 0/1:

```c
power_raw = sum_cached_poe_port_power();
if (state == 0 && power_raw < 1460) state = 1;
else if (state == 1 && power_raw >= 1501) state = 0;
write_gpio27(state);
```

**GPIO26 is not an input to this decision.** The input/LED routine neither
writes the control state nor calls the GPIO27 writer. Thus this stock path has
no fan-stall retry or boost triggered by the input. It also has no RPM target,
temperature curve, per-fan selection or percentage setting. Initialization
writes GPIO27=0; subsequent low-load polling changes it to 1. A timed fan-start
boost was not found in this path.

The combined poll was executed with both GPIO26 levels, both LED-enable values,
both previous control states and four PoE loads: **32 cases passed**. Changing
GPIO26 changed the two index-0 LED modes, but not the GPIO27 result for a given
load/state. LED output 26, **index 1**, belongs to the separate PoE-budget
indicator; do not confuse it with the index-0 pair. LED output numbers and GPIO
bit numbers are separate namespaces.

## Search for another GPIO output

The main GPIO writer `0xbf0196b4` has 23 direct `j`/`jal` references in the
scanned startup/runtime ranges. Manual instruction tracing groups them as:

| Output bit | Callers / file offsets | Observed code role |
| --- | --- | --- |
| 22 | `0x17590` | Low output in the reset/watchdog path |
| 24 | `0x54634`, `0x54648` | Low/high pulse in PoE initialization; startup also sets bit 24 directly at `0x480` |
| 27 | `0x54358`, `0x544dc` | Automatic-policy wrapper and output initialization |
| 28, 29 | Remaining 18 references | Clock/data transitions in the external-device bus |

Two other GPIO-data helpers, `0xbf01978c` and `0xbf019864`, have no direct
`j`/`jal` callers or aligned literal pointers in this image scan. That is a
bounded reference search, not a proof against every computed indirect call.
No second fan-specific output was identified in these paths.

## External devices on GPIO28/29

The transaction code implements a software I²C-style bus: GPIO28 is clock,
GPIO29 is data. It sends `(address << 1) | direction`, an 8-bit register index,
data and ACK bits; reads use a repeated START. The address table at file
`0xcb670` contains **0x20, 0x21, 0x22, 0x23**.

| Routine | Address | Operation |
| --- | --- | --- |
| START / STOP | `0xbfc5c3fc` / `0xbfc5c454` | Bus framing |
| Send / receive bits | `0xbfc5c4f4` / `0xbfc5c6a4` | GPIO28/29 bit operations |
| Register write / read | `0xbfc5c7a8` / `0xbfc5ca08` | Address, register, byte transaction |
| Device-index write / read | `0xbfc5c904` / `0xbfc5cbd8` | Index 0–3 translated through the address table |
| Block read | `0xbfc5d0f8` | Multiple bytes from one device |

These transactions feed the existing 16-port PoE records: four devices, four
channels each, with channel order remapped to physical port numbers in the
software. The measurement consumer at `0xbfc5d2ac` reads 18 bytes starting at
register `0x40`; the status consumer at `0xbfc5dd5c` reads registers `0x2a`,
`0x25`, `0x2e`, `0x30`, `0x32`, and a four-byte block at `0x26`.

Initialization at `0xbfc5d028` writes these register/value pairs to each device:

```text
07=0f  0c=0f  55=af  54=00  0f=06  03=aa  01=83
13..16=04; 17..1a=01
```

Execution with successful mocked bus replies confirmed **60 writes and four
reads** during full PoE initialization. Normal port-control paths also write
`0x05`, `0x06` and `0x11`. The periodic recovery check compares register `0x01`
with `0x83` and reads `0x21`; `0x83` is also written by initialization, so it
must not be presented as a discovered chip ID.

No fan PWM/RPM command was identified among these callers. The exact external
chip model and its complete register semantics remain unestablished. A generic
I²C address or a register map for another PSE is insufficient to name the chip
or justify changing undocumented registers.

## What GPIO26 can provide

The v0.1.2 implementation already exports `cooling.gpio26_level` and prints it
in `cool status`. Hardware CLI output is confirmed; a v0.1.2 JSON response has
not yet been supplied. The software relationship is:

| GPIO26 | LED output 26, index 0 | LED output 27, index 0 |
| --- | --- | --- |
| 0 | Mode 0 | Mode 5 |
| 1 | Mode 5 | Mode 0 |

This assumes LED enable at RAM `0xbf0023d0` is nonzero. When disabled both modes
are 0. The owner's observation of GPIO26=0 with orange FAN is one correlation;
there is no corresponding observation with both fans starting normally.

Useful next features, **not implemented by this investigation**:

- Record changes of the raw input and timestamps in the collector; display
  input level and its history without inventing RPM or fault polarity.
- Expose the software-selected indicator modes and their enable flag, keeping
  them distinct from a measured front-panel color or individual fan state.
- After correlating the input with a naturally healthy and failed condition,
  derive an aggregate cooling alarm, add debounce, and alert from monitoring.
- Consider an automatic recovery policy only after establishing which output
  level helps and what the input means. The stock LED path does not do this.

One sampled bit does not establish two fan identities or RPM. GPIO26 must remain
an input: writing its direction/data is not a method of increasing fan speed.
Changing the software LED display alone would not fix the stopped fan.

## Consequence for a firmware fix

The code establishes two output levels. Lowering the PoE thresholds, forcing
the high-load branch, or holding GPIO27=0 longer would reuse the same output
already reached by `cool test 0`; it would not create a higher voltage or a
third speed. The confirmed active readback therefore rules out “the command
never changed the register” as the explanation for that observation, but it
does not establish why the fan did not start.

No additional software speed control was found in the reviewed paths. The
physical fan circuit could contain autonomous behavior outside this runtime;
this code analysis cannot establish its wiring or the failing fan's condition.

## Reproduce

```bash
python3 tools/audit_cooling_paths.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin > research/cooling-paths-evidence.json
```

Requires `requirements-dev.txt`. [Evidence JSON](cooling-paths-evidence.json)
includes SHA-pinned block hashes, the direct-reference inventory, explicit
mocked functions, initialization transactions and all 32 poll cases. No device
is accessed. [Original analysis](COOLING.md) · [v0.1.2 commands](../docs/COOLING-CONTROL.md).
