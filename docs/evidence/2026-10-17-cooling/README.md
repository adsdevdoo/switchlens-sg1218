**English** | [Русский](README.ru.md)

# Confirmed shared fan-speed effect

## Hardware update — 17 October 2026, 21:46 Europe/Belgrade

The owner replaced the fan that needed a push with a stock fan. Both installed
fans now rotate normally, and `cool test 0` makes **both rotate faster**. The owner
corrected an initial mention of `cool test 1` to `cool test 0`.

This establishes an observed shared speed effect of GPIO27=0 on this unit. It
supersedes the earlier inconclusive tests and the hypothesis that the output only
enables the second fan. It does not establish RPM, supply voltage, the electrical
circuit, maximum attainable speed, or the cause of the removed fan's startup issue.
Do not describe the current unit as having a stopped fan or assume both installed
fans are Noctua. The other fan's exact current identity is not restated here.

The existing v0.1.2 JSON already exposes `cooling.gpio27_level` and `cooling.mode`.
For this verified unit, a consumer may label a valid GPIO27 output level 0 as
**higher-speed request**, and level 1 as **lower-speed request**. These labels
represent the commanded mode, not measured rotation or fan health. Check GPIO
mux/direction and reject null/invalid data rather than treating it as low speed.
Keep `fan_rpm` and `fan_status` unknown. `mode=auto` describes the control policy,
not speed: auto can select either output. No schema or released BIN changes.

Current action: use `cool auto` to return to the stock PoE-dependent policy and
use existing telemetry for mode monitoring. Neither a startup boost nor repeated
GPIO tests are needed to address the now-replaced fan. Exact timer calibration
remains independent work and is no longer a prerequisite for proving the speed effect.
