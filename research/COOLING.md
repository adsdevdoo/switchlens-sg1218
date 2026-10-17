**English** | [Русский](COOLING.ru.md)

# Cooling investigation and board-signal statistics

Update 17 October 2026: [v0.1.2 with cool and cooling JSON](../docs/COOLING-CONTROL.md)
is prepared; 24 MIPS tests pass and its hardware test is pending. The analysis
below concerns the original code and v0.1.1, whose BIN is unchanged. The new
test does not assign fan-speed names to GPIO levels.

## What is established

The stock runtime has a **PoE-load-dependent binary output on GPIO27** and an
**input on GPIO26 that selects LED modes**. Both paths execute in the PoE polling
chain. They are candidates for cooling control and fault indication, but their
connections to the fan circuit have not been confirmed. GPIO numbers here are
bit indices in the firmware register, not connector pins or Linux GPIO numbers.

| Evidence | Result | Limit |
| --- | --- | --- |
| SHA-pinned firmware disassembly | GPIO27 output, GPIO26 input, PoE hysteresis and LED calls | Does not identify physical fan wiring |
| Original MIPS instructions in Unicorn | Thresholds, state history, LED arguments and read-command syntax verified | Synthetic hardware values, no actual fan |
| Owner's observations | Same Noctua fails to start on either header; runs after a manual push | Supply voltage, waveform and tach signal not measured |
| Installed `/stats.json` | Existing system, port and PoE statistics work | No fan state, RPM or temperature fields |

The owner fitted Noctua NF-A4x20 PWM, 12 V, four-wire fans with only the standard
three connections reported connected: ground, supply and tachometer. The fourth
PWM input is unconnected. This is a wiring report, not a verified board pinout.
One fan twitches without starting; the symptom follows that fan when headers are
swapped. Running after a push suggests a startup problem, but does not distinguish
insufficient supply from a mechanical/electronic fault in that fan.

## Output logic: GPIO27

The 20230616 stock image and released v0.1.1 contain identical instructions in
the ranges below. [Machine-readable evidence](cooling-evidence.json) records
stock SHA-256 and hashes of each half-open file range.

| Item | Address / file offset | Behavior |
| --- | --- | --- |
| GPIO control | `0xb8003500` | Pin function selection |
| GPIO direction | `0xb8003508` | Bit 0 = input, bit 1 = output |
| GPIO data | `0xb800350c` | GPIO26 mask `0x04000000`; GPIO27 mask `0x08000000` |
| Combined setup | `0xbfc5c66c`, file `0x5466c..0x546a4` | GPIO26 input; GPIO27 output initially 0 |
| Output setup | `0xbfc5c49c`, file `0x5449c..0x544f4` | Configures GPIO27 and writes initial level |
| Controller | `0xbfc5c368`, file `0x54368..0x543fc` | Sums PoE power; updates hysteresis state |
| Output wrapper | `0xbfc5c344`, file `0x54344..0x54368` | Accepts 0/1 and calls GPIO writer |
| GPIO writer | `0xbf0196b4`, file `0x32ec..0x3328` | Read-modify-write of one data bit |
| Control state | RAM `0xbf014840`, uint32 | 0 or 1 in the normal path |
| Total PoE power | RAM `0xbf014400` | Same aggregate used by `poe.consumption_raw` |

The controller sums signed 16-bit values at `0xbf0143e0 + 48*i + 10`, including
both configured endpoint indices (normally ports 1–16). Existing PoE analysis
identifies the raw unit as 0.1 W. Its exact state transition is:

| PoE sum, raw | Power | Next state / GPIO27 level |
| --- | --- | --- |
| `< 1460` | `< 146.0 W` | 1 |
| `1460..1500` inclusive | `146.0..150.0 W` | Keep previous state |
| `>= 1501` | `>= 150.1 W` | 0 |

This table assumes a previous state of 0 or 1. Unexpected states are preserved
by this function and rejected by the output wrapper; the decoder reports them
without converting them to a valid mode. Initialization writes output 0; a later
low-load poll can change it to 1.

The call at file `0x56798` reaches `0xbfc5e2fc`, which calls the input/LED routine
at `0xbfc5e0a4` and this controller. The controller uses power and previous state;
it does not read RPM or temperature. This is binary switching, not a generated
25 kHz fan PWM signal. The physical voltage/speed corresponding to levels 0/1,
and whether this output actually controls both fans, remain unverified.

## Input logic: GPIO26

Function `0xbfc5e0a4` (file `0x560a4..0x56184`) reads GPIO26 through
`0xbf0196f0` and selects opposite mode arguments for two LED outputs. With its
enable argument nonzero, calls to `0xbfc26830` use:

| GPIO26 level | LED output 26, index 0: mode | LED output 27, index 0: mode |
| --- | --- | --- |
| 0 | 0 | 5 |
| 1 | 5 | 0 |

With enable 0, both mode arguments are 0. LED output numbers are a separate
namespace from GPIO bit numbers. The enable argument comes from `0xbf0023d0`,
initialized to 1. No edge count, pulse period or RPM calculation exists in this
routine. The front-panel LED identity, alarm polarity and possible aggregation
of two fan tach signals still need checking. A sampled high/low bit cannot be
reported as measured RPM or as proof that a particular fan is running.

## Historical v0.1.1 read procedure

Archived syntax, not the current next step. [New procedure](../docs/COOLING-CONTROL.md).

At `RTK#`, enter each command separately, without copying the prompt:

```text
reg socget 0x3508
reg socget 0x350c
reg flashget 0x14840 0
```

These exact commands were executed through the original CLI parser in the
emulator, with the relevant GPIO and RAM pages protected against writes.
`socget` reads `0xb8000000 | offset`. Despite its name, this `flashget` branch
reads one word at `0xbf000000 | offset`, here the RAM state `0xbf014840`.

Two stock CLI quirks matter:

- Use `socget` without `--`. `reg --socget ...` prints help in this image even
  though the help text advertises that spelling.
- The last **read** prints `set flashreg ...`. This is a misleading stock output
  string; the selected single-word branch executes a load. It does not write
  flash or change fan control. Do not substitute `flashset` or `socset`.

Capture one set of three replies while the problematic fan is naturally stopped.
Note which fan is stopped, the other fan's state, the front FAN indicator and
current `poe.consumption_raw`. If the problematic fan is subsequently running,
capture another set and the same observations. Do not deliberately stall a fan
or create a high PoE load for this comparison. Rewiring is unnecessary.

Direction `0x39000000` and data `0x39780000` were supplied; a complete state read
was not. One fan runs, one is stopped and FAN is orange. Truncated `flashget`
hung the old console; use the short `cool` procedure in v0.1.2 for current testing. Repeated readings
can expose correlation, but an unchanged input cannot alone prove that fan
monitoring is absent. Physical tracing or tach measurements may still be needed.

## Turn copied readings into diagnostic JSON

Save **one observation** in a UTF-8 text file, then run from the repository root:

```bash
python3 tools/decode_board_signals.py observation.txt --label fan-stopped > observation.json
```

Python's standard library is sufficient. The tool has no serial, network or
device access. It requires exactly one result per address and rejects duplicate,
missing, oversized or wrong-kind results so separate observations are not mixed.
Unrelated boot text is ignored. The parser accepts the stock `set flashreg`
wording; a pasted transcript is not independent proof of which command was run.

For example, these are **synthetic test values**, not readings from the owner:

```text
get socreg 0xb8003508 = 0x8000000
get socreg 0xb800350c = 0xc000000
set flashreg 0xbf014840 = 0x1
```

They decode to GPIO26 = 1, GPIO27 = 1, input/output directions as expected and
control state 1. Neither fan health nor RPM is inferred.

| JSON field | Meaning |
| --- | --- |
| `diagnostic_version` | Decoder format version, currently 1; independent of `/stats.json` schema |
| `source` | `copied_uart_text` |
| `label` | Optional operator text; null if omitted |
| `capture_time` | Null: the decoder does not invent a measurement timestamp |
| `atomic_snapshot` | False: the three commands execute sequentially |
| `registers_raw` | Three original uint32 values formatted as hexadecimal strings |
| `signals.gpio26_level_raw` | Data bit 26, integer 0/1 |
| `signals.gpio27_level_raw` | Data bit 27, integer 0/1 |
| `signals.gpio26_configured_as_input` | Direction bit 26 is zero |
| `signals.gpio27_configured_as_output` | Direction bit 27 is one |
| `signals.poe_load_control_state_raw` | Raw uint32 at `0xbf014840` |
| `signals.poe_load_control_state_valid` | State is 0 or 1 |
| `signals.output_matches_state` | GPIO27 equals valid state; null for another state |
| `fan_mapping_verified` | False until hardware mapping is established |
| `fan_status`, `fan_rpm` | Null: neither is measured by this decoder |

Directions describe direction bits only; they do not independently verify pin
multiplexing. A state/data mismatch can arise between sequential reads and is
not itself a fan fault. Do not merge this diagnostic format into the current
`/stats.json` response or treat it as a new firmware release.

## What is needed for fan statistics and startup diagnosis

1. Match GPIO26 changes to actual fan states and the front indicator. Establish
   whether it is an aggregate alarm and determine polarity before naming it.
2. Trace GPIO27 to the fan supply/control circuit and establish the electrical
   meaning of both levels before exposing a cooling mode or changing thresholds.
3. For RPM, establish whether individual tach signals reach readable inputs and
   how pulses can be counted with a known time base. One binary alarm is insufficient.
4. Add only established fields to a future read-only endpoint implementation,
   with schema, serializer, emulator checks and an identified new BIN. Reading
   statistics must never force a GPIO or alter cooling policy.

Noctua specifies 12 V operation and 8 V starting voltage for this model. Its
manual supports three-pin operation: with PWM unconnected it normally runs at
full speed unless the supply voltage is regulated. Therefore a low-voltage
board mode is a plausible startup explanation, **not a measured diagnosis**.
Testing that fan on a known appropriate 12 V source would separate a supply
issue from a fan fault; do not apply 12 V to the tach or PWM input.

Noctua's tach output provides two pulses per revolution (`RPM = Hz × 30`). This
describes the fan, not the switch's ability to measure it. Manufacturer references:
[model specifications](https://www.noctua.at/en/products/nf-a4x20-pwm/specifications),
[installation manual](https://cdn.noctua.at/media/noctua_nf_a4x20_pwm_manual_en_web.pdf),
[PWM/tach white paper](https://cdn.noctua.at/preview/media/Noctua_PWM_specifications_white_paper.pdf).
The [Linux Realtek GPIO driver](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-realtek-otto.c)
provides register-layout context; its board-independent definitions do not prove
this board's wiring.

## Reproduce the firmware checks

Install `requirements-dev.txt` for Unicorn, then run from the repository root:

```bash
python3 tools/audit_cooling.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin > research/cooling-evidence.json
python3 tests/test_board_signals.py --report research/board-signals-test-results.json
```

[Seven passing tests](board-signals-test-results.json) cover both hysteresis
boundaries, history and summation, preservation of unrelated GPIO bits, the LED
truth table, full CLI parsing with protected read targets, incorrect `--` syntax,
decoder rejection paths and the audit's SHA gate. The tests execute original
MIPS instructions with synthetic registers; they do not establish physical fan
mapping, actual supply levels, sustained thermal behavior or hardware read results.
