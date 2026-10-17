**English** | [Русский](COOLING-CONTROL.ru.md)

# Cooling commands — v0.1.3

| Command | Behavior |
| --- | --- |
| `cool low` | Both fans: lower-speed output, no timeout |
| `cool fast` | Both fans: higher-speed output, no timeout |
| `cool auto` | Stock automatic PoE policy |
| `cool status` | Show mode and raw input/output state |

Manual modes last until another command or reboot. There is no `cool test` command.
`auto` uses thresholds <1460 and >=1501 in 0.1 W units, retaining prior state in
between. GPIO27=0 is the observed faster setting. GPIO26 drives stock LED selection;
indicator color/individual health/RPM are not inferred. No flash setting is written.

`cooling.mode` reports auto/manual/invalid; `cooling.speed_mode` reports low/fast/null.
JSON only reads; it never changes a fan mode. The endpoint is public in v0.1.3.

[v0.1.3: BIN, implementation / реализация, checks / проверки](../releases/v0.1.3-public-stats/README.md).

[Historical v0.1.2 / История v0.1.2](../releases/v0.1.2-cooling/README.md); [hardware evidence / аппаратное подтверждение](evidence/2026-10-17-cooling/README.md).
