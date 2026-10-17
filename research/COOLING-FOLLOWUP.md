**English** | [Русский](COOLING-FOLLOWUP.ru.md)

# Cooling follow-up: bootloader, timer and four vendor builds

17 October 2026. This extends the [GPIO inventory](GPIO-INVENTORY.md).
No additional fan-speed control was identified in the paths below. The new
evidence narrows specific remaining possibilities; it does not prove the absence
of every computed hardware access or identify the physical fan power circuit.
No firmware or hardware was changed.

## Four versions contain the same binary-output policy

The identified controller in every archived official V5 build was executed
using its original MIPS instructions. Only the final GPIO writer was mocked.
Each image is SHA-256 pinned in [the analysis tool](../tools/audit_cooling_followup.py).

| Build | Wrapper file offset | Controller file offset | Cases passed |
| --- | --- | --- | --- |
| 20220921 | `0x541d4` | `0x541f8` | 20 |
| 20221012 | `0x54294` | `0x542b8` | 20 |
| 20230220 | `0x54c34` | `0x54c58` | 20 |
| 20230616 | `0x54344` | `0x54368` | 20 |

All **80 cases** passed: both normal previous states, eight raw loads including
both transition boundaries and a negative signed sample, plus invalid-state
cases. All versions use GPIO27 and the same hysteresis:

- Previous 0 and sum below 1460: write 1.
- Previous 1 and sum at least 1501: write 0.
- Between those boundaries: keep the previous state.
- A state other than 0/1 is preserved and rejected by the output wrapper.

The code addresses differ; the tested behavior matches. This comparison is of
the identified controller, not an assertion that the whole images are identical
or that every other routine was compared. It provides no reason to downgrade
to obtain a different setting in this controller. Its output still has only two
levels, whose physical effect on the fan headers is unconfirmed.

## Bootloader setup

The source is the first `0x8000` bytes of the archived original SPI export.
The full export SHA-256 is
`b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87`;
the boot prefix SHA-256 is
`ef95ee8dc73b39f97300366c0d41e3ff796572fed14e10d21a04ee48f1edf7b6`.

The GPIO setup slice at boot offsets `0x5c98..0x5cf4` clears CNR bit 24, sets
direction bit 24 and sets data bit 24. It also clears switch-register bit 15
at `0xbb00a000`. Executing all 23 instructions with three different initial
GPIO words confirmed that GPIO27 and all other GPIO bits remain unchanged.
No functions are mocked in that slice. Flash erase/recovery routines are not
executed by this audit.

A separate static review of the 19 matching SoC-base constructors in the boot
prefix found no additional GPIO setup beyond that block. Other reviewed paths
address SPI, interrupt, timer and UART registers. This is not a full bootloader
emulation or proof against arbitrarily constructed addresses. No bootloader
fan PWM/startup-boost routine was identified.

## Timer and the meaning of 100 ticks

The runtime initializes and starts timer index 0 through `0xbfc104b0` and
`0xbfc10504`. The only direct callers found are at file `0x86c4` and `0x86cc`.
The ISR `0xbf01a094` is registered using a constructed function pointer at
`0x86f8..0x86fc`.

Executing the original initialization and 100 ISR invocations with synthetic
MMIO confirms:

| Item | Result |
| --- | --- |
| Fast counter `0xbf002e94` | Advances by 100 |
| Uptime counter `0xbf002e90` | Advances by 5 |
| ISR peripheral access | Only timer register `0xb800310c` in the monitored `0xb8003000..0xb8003fff` window |
| GPIO reads/writes in the ISR | None |

The ISR updates counters and scheduler flags. GPIO changes can still occur in
tasks called later by the scheduler; the PoE controller is one such path. These
results exclude GPIO waveform generation inside this particular ISR, not every
possible hardware waveform source.

v0.1.2 `cool` uses the **fast counter**, whereas `system.uptime_ticks_raw` uses
the divided counter. Therefore its 100-tick limit equals five raw uptime
increments when starting on a divider boundary. Under the existing, unverified
200 MHz timer-clock assumption this is approximately five seconds. The 20:1
counter ratio is established by code; the wall-clock duration is not calibrated.
The emulator does not simulate a running physical timer.

## Other computed paths and names

The generic SoC read/write helpers at `0xbfc107ec`, `0xbfc10810` and
`0xbfc10824` have no direct, aligned-literal or nearby constructed references
in the bounded scan. The masked writer `0xbfc10848` has the configuration-table
caller at file `0x27ffc`; the six relevant default records were already found
disabled in the GPIO audit. Explicit UART register commands remain a separate
way to write arbitrary registers, not an automatic fan-control policy.

The external serial-bus initializer `0xbfc11590` has the optical-module caller
and a wrapper `0xbfc11614`. The wrapper has no references found by the same
bounded methods. The resolved external-GPIO callback path remains the optical
module path documented in the previous audit.

ASCII string searches for delimited fan/fans/thermal/PWM/tach/temperature/cooling
names found no matches in the June runtime or boot prefix. Missing strings do
not prove missing functionality in a stripped binary.

## Practical result

The investigated code supports a two-level GPIO27 policy; a third setting,
per-fan speed target or additional PWM control was not found. Reusing another
vendor build's identified controller would not add such a setting. A longer
GPIO27 hold would extend the same level already tested, not establish a higher
electrical output.

The remaining hardware question is how the fan connectors receive power and
how their feedback reaches the board. The existing overview photo does not
establish those connections or readable markings of every nearby component.
Clear close-ups of both fan connectors, nearby components and the corresponding
back side would support tracing that path without electrical measurements.

## Reproduce

With `requirements-dev.txt` installed and the archived vendor BINs/export present:

```bash
python3 tools/audit_cooling_followup.py > research/cooling-followup-evidence.json
```

[Evidence JSON](cooling-followup-evidence.json) contains hashes, all 80 policy
cases, boot register accesses, timer results and reference-search candidates.
