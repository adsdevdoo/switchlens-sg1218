**English** | [Русский](JSON-API.ru.md)

# `/stats.json` reference — schema 1

For **SwitchLens 0.1.1 working firmware**, 17 October 2026, on TP-Link
TL-SG1218MPE(UN) V5.0. Boot, UART help and two complete JSON replies with changing
counters were observed on the owner's unit. [Hardware evidence](evidence/2026-10-17-switchlens/README.md).

This document describes the implementation. Authoritative structure:
[JSON Schema 2020-12](../schema/stats.schema.json). Value sources:
[adapter](../target/adapter.c), [MIB reader](../src/sg_mib.c),
[serializer](../src/sg_stats.c), [evidence map](../research/metric-sources.json).
The earlier `research/JSON-CONTRACT.txt` is a historical design record.

## Request and authentication

1. Log in to the stock switch web interface.
2. Open `http://<switch-address>/stats.json` in the same browser.
3. Save the entire response, not only the visible portion of the page.

The handler matches the exact `GET /stats.json` path and uses the existing
`H_P_SSID` session. It does not add a login or API token. If a login page appears,
sign in again. HTML is a collection error even with status 200. Query strings
and alternative paths are outside this handler's contract.

The successful handler sets these headers in code:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
X-SwitchLens-Build: experimental-1
```

The screenshots establish receipt of the body; a hardware packet capture of
these headers was not supplied. The historical `experimental-1` header identifies
the shared HTTP payload, not the exact installed package; both v0.1.0 and v0.1.1 use it.

With an already established session cookie jar:

```bash
curl --fail --max-time 15 -b /private/bench.cookies \
  http://SWITCH_IP/stats.json -o stats.json
python3 -m json.tool stats.json
```

The cookie jar comes from a separate normal login. Do not publish passwords or
cookies. Reading this endpoint does not change configuration, reset counters,
switch PoE or store JSON in flash. The enabled stock UART CLI separately contains
commands that can modify device settings.

## Types, missing values and response integrity

| Value | Consumer interpretation |
| --- | --- |
| `null` | Unavailable, unimplemented, unconfirmed, failed read or inapplicable; the reason depends on the field |
| `0`, `0.0`, `"0"` | A returned zero in the field's type; not a replacement for null |
| `false` | A returned negative Boolean state, for example link down |
| `"528836"` | An unsigned decimal counter string, not a JSON number |

All schema keys are present. Counter strings have no sign or leading zeroes,
except `"0"`. Their maximum is `18446744073709551615` (`uint64`). The schema regex
limits digit count; clients must additionally enforce this numeric maximum.
Use JavaScript `BigInt` or Python `int`; converting large counters to JavaScript
`Number` can lose precision.

Fields and ports are read sequentially, not as one atomic hardware snapshot.
Separately read categories may not exactly sum to a separately read aggregate.
PoE comes from stock RAM cache with unknown refresh timing. Schema support does
not establish hardware accuracy for every field.

Transport failures can produce a truncated response. Accept only complete JSON
of the expected schema; do not publish partially collected values. The handler's
deadline uses raw ticks, not confirmed seconds.

## Root object

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | integer, always `1` | JSON contract version, not firmware version |
| `system` | object | Device identity and network information |
| `poe` | object | Global PoE information |
| `ports` | array, exactly 18 items | Ports ordered 1–18 |
| `loop_prevention` | object | Raw software loop-detection masks |

A `?` suffix in the following tables means the field also permits `null`.

## `system`

| Field | Type | Meaning and limits |
| --- | --- | --- |
| `model` | string? | Adapter constant `TL-SG1218MPE`, not generic model detection |
| `hardware_version` | string? | Full stock hardware string, e.g. `TL-SG1218MPE 5.0` |
| `firmware_version` | string? | Full stock build string, up to 64 source bytes; preserved as `1.0.0 Build 20230616 Rel.57668` |
| `name` | string? | Compatibility alias of `description`, not an independent hostname |
| `description` | string? | Editable Device Description, up to 32 source bytes; JSON escaped |
| `mac` | string? | Switch MAC read through ASIC registers, `xx:xx:xx:xx:xx:xx` |
| `uptime_seconds` | number? | Currently always null: tick-to-seconds scale unconfirmed |
| `uptime_ticks_raw` | integer? | 32-bit value at RAM `0xbf002e90`, 0–4294967295; can wrap; time unit unconfirmed |
| `ip_address` | string? | Current management IPv4 from RAM |
| `subnet_mask` | string? | IPv4 subnet mask |
| `default_gateway` | string? | IPv4 default gateway |

The unchanged stock firmware string after an upgrade is not proof of rollback.
The installed variant is associated with installation evidence, behavior and,
when required, image readback. This string alone does not identify SwitchLens.

## Global `poe`

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `budget_w` | number?, W | Configured system power limit from cache; raw / 10 |
| `consumption_w` | number?, W | Cached total consumption; raw / 10, not clamped down to budget |
| `remaining_w` | number?, W | Calculated `max(budget_w - consumption_w, 0)` |
| `consumption_raw` | integer? | Original nonnegative consumption before division by 10 |
| `recovery_enabled` | Boolean? | Global stock PoE Auto Recovery flag; unsupported code becomes null |

The bench returned 250 W budget, 0 W consumption, 250 W remaining. This is a
reported idle condition, not a loaded calibration or proof of maximum PSU output.

## `ports[]`: link and configuration

| Field | Type | Meaning |
| --- | --- | --- |
| `port` | integer 1–18 | JSON port number in fixed array order |
| `admin_enabled` | Boolean? | Administrative enable setting, not link presence |
| `link_up` | Boolean? | Current reported link state |
| `speed_config_code` | integer? | Configured-mode code decoded from stock configuration bits; not Mbps |
| `speed_actual_code` | integer? | Actual-state code listed below |
| `speed_mbps` | 10, 100, 1000 or null | Current link Mbps; null for no link, read error or unsupported code |
| `duplex` | `half`, `full` or null | Link duplex; null for no link or read failure |
| `flow_control_configured` | Boolean? | Configured flow control |
| `flow_control_active` | Boolean? | Link up and both RX/TX flow-control bits set; not a pause-frame count |
| `lag_id` | integer? | Currently null: aggregation group mapping not implemented |
| `counters` | object | The 49 counter fields described below |
| `poe` | object or null | Object on ports 1–16, null on ports 17–18 |

Adapter mapping: JSON ports 1–16 → ASIC 0–15, port 17 → 24, port 18 → 25.
This is established code behavior; independent checking of every front-panel
connector remains pending. Boot lines `set port 24…27` are not sufficient to
establish front-panel numbering.

| `speed_actual_code` | Adapter interpretation |
| --- | --- |
| 0 | No link |
| 1 | Other/unusual speed–duplex combination not listed below |
| 2 | 10 Mbps, half |
| 3 | 10 Mbps, full |
| 4 | 100 Mbps, half |
| 5 | 100 Mbps, full |
| 6 | 1000 Mbps, full |
| null | State read failed |

Do not apply this table to `speed_config_code`: the encodings differ. The real
port-1 sample has config=5, actual=6, speed=1000, duplex=full. Matching all
configured modes to the stock UI remains pending.

## `ports[].counters`

Every value is a decimal string or null. RX/TX are **from the switch's perspective**.
These are accumulated totals, not bytes/packets per second. The endpoint has no
reset operation.

The selector column identifies the investigated stock getter path. The adapter
uses its own error-checked reader, not the problematic stock getter. Individual
register counters are read as 32-bit words; byte counters use two words with up
to three high–low–high attempts. This describes the read method, not proof of
actual hardware width or absence of read side effects in every ASIC mode.

### Traffic and aggregates

| Field | Meaning | Selector / construction |
| --- | --- | --- |
| `rx_bytes` | Received bytes | 1, two words; inclusion of FCS/overhead not established by bench tests |
| `tx_bytes` | Transmitted bytes | 9, two words; exact byte accounting also needs comparison |
| `rx_good_packets` | Stock received-packet aggregate | RX unicast + multicast + broadcast, own 64-bit addition |
| `tx_good_packets` | Stock transmitted-packet aggregate | TX unicast + multicast + broadcast, own 64-bit addition |
| `rx_bad_packets` | Stock-web-compatible aggregate | Formula below; not standard ifInErrors |
| `tx_bad_packets` | Stock TxBadPkt | 21, same source as `tx_excessive_collisions` |
| `rx_unicast_packets` | Received unicast | 2 |
| `rx_multicast_packets` | Received multicast | 4 |
| `rx_broadcast_packets` | Received broadcast | 6 |
| `tx_unicast_packets` | Transmitted unicast | 10 |
| `tx_multicast_packets` | Transmitted multicast | 12 |
| `tx_broadcast_packets` | Transmitted broadcast | 14 |
| `tx_drop_packets` | Stock transmit discard counter | 16 |
| `rx_discards` | General receive discards | Always null: no verified source/non-overlapping sum |

The actual `rx_bad_packets` formula preserves unusual stock UI behavior:

```text
((rx_oversize_packets + tx_oversize_packets) mod 2^32)
+ ((rx_undersize_packets + tx_undersize_packets) mod 2^32)
+ rx_jabbers + rx_fragments + rx_crc_align_errors
```

It contains TX categories. Do not relabel it as a standard receive-error total
or add its components again. Sequential reads also mean separately retrieved
components and aggregates need not match exactly.

### Additional MIB categories

Their register paths were verified statically. **The following names/meanings
were matched against the RTL838x family map and remain provisional on this board.**
A zero sample is not an independent test of the corresponding error condition.

| Field | Proposed meaning | Selector |
| --- | --- | --- |
| `rx_bridge_discards` | Bridge-layer discards | 125 |
| `rx_mac_discards` | MAC discards | 84 |
| `rx_undersize_drops` | Dropped undersized frames | 65 |
| `rx_crc_align_errors` | CRC/alignment errors | 31 |
| `symbol_errors` | Symbol errors | 22 |
| `rx_unknown_control_opcodes` | Unknown control opcodes | 23 |
| `rx_pause_frames` | Received pause frames | 24 |
| `tx_pause_frames` | Transmitted pause frames | 25 |
| `drop_events` | Discard events, not necessarily packet count | 26 |
| `rx_undersize_packets` | Received undersize category | 35 |
| `tx_undersize_packets` | Transmitted undersize category | 36 |
| `rx_oversize_packets` | Received oversize category | 38 |
| `tx_oversize_packets` | Transmitted oversize category | 39 |
| `rx_fragments` | Fragments/errored short frames | 40 |
| `rx_jabbers` | Jabber category | 43 |
| `collisions` | Collisions | 46 |
| `tx_single_collision_frames` | Frames with one collision | 17 |
| `tx_multiple_collision_frames` | Frames with multiple collisions | 18 |
| `tx_deferred_transmissions` | Deferred transmissions | 19 |
| `tx_late_collisions` | Late collisions | 20 |
| `tx_excessive_collisions` | Excessive collisions | 21 |

Categories may overlap; do not sum them arbitrarily into “all losses.” Increasing
`rx_bridge_discards` alone does not identify loss cause or cable condition.
It changed from 163 to 3870 in the real samples; the cause remains unknown.

### Frame-size distribution

These are separate ranges, **not cumulative Prometheus histogram buckets**.
Exact FCS accounting and the upper `max` bound need hardware verification.

| RX field | TX field | Size category, bytes | RX/TX selector |
| --- | --- | --- | --- |
| `rx_packets_64` | `tx_packets_64` | 64 | 48 / 49 |
| `rx_packets_65_127` | `tx_packets_65_127` | 65–127 | 51 / 52 |
| `rx_packets_128_255` | `tx_packets_128_255` | 128–255 | 54 / 55 |
| `rx_packets_256_511` | `tx_packets_256_511` | 256–511 | 57 / excluded |
| `rx_packets_512_1023` | `tx_packets_512_1023` | 512–1023 | 60 / 61 |
| `rx_packets_1024_1518` | `tx_packets_1024_1518` | 1024–1518 | 63 / 64 |
| `rx_packets_1519_max` | `tx_packets_1519_max` | 1519–maximum | 66 / 67 |

`tx_packets_256_511` is always null: stock selector 58 fails to write the low
output word. A new independent source has not been verified. Do not derive it
by subtracting other counters collected at different times.

## `ports[].poe`

Ports 17–18 have `poe: null` as a whole. For ports 1–16, `enabled: true` and
`status: "OFF"` can coexist: configuration permits power while the reported
supply state is off.

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `enabled` | Boolean? | PoE enable value from stock cache |
| `status_code` | integer? | Raw state code, retained even when unknown |
| `status` | string? | Decoded state below; unknown code becomes null |
| `power_w` | number?, W | Positive signed16 raw power / 10 |
| `current_ma` | number?, mA | Positive signed16 current, unscaled |
| `voltage_v` | number?, V | Positive signed16 raw voltage / 10 |
| `measurements_valid` | Boolean? | Currently null: independent validity/freshness flag not established |
| `pd_class` | integer 0–4? | Powered-device class decoded from known raw code |
| `pd_class_raw` | integer? | Original class code, including unknown values |
| `priority_code` | integer? | 0 High, 1 Middle, 2 Low; other values left undecoded |
| `power_limit_mode` | `auto`, `fixed` or null | Raw 330 means auto; other nonnegative values mean fixed |
| `power_limit_w` | number?, W | Fixed raw limit / 10; null in auto mode |
| `extend_enabled` | Boolean? | Currently null: source not implemented |
| `recovery` | object | Auto Recovery configuration and raw statistics |

Zero and negative **per-port** power/current/voltage readings become null because
the stock UI displays `---` for zero. This does not apply to global consumption,
where zero is retained. Power, current and voltage are not derived from each other.

| Code | State | Stock-table meaning |
| --- | --- | --- |
| 0 | `OFF` | Off |
| 1 | `TURNING-ON` | Turning on |
| 2 | `ON` | On |
| 3 | `OVERLOAD` | Overload |
| 4 | `SHORT` | Short circuit |
| 5 | `NOSTANDARD-PD` | Non-standard powered device |
| 6 | `VOLTAGE-HIGH` | High voltage |
| 7 | `VOLTAGE-LOW` | Low voltage |
| 8 | `HARDWARE-FAULT` | Hardware fault |
| 9 | `OVERTEMPERATURE` | Overtemperature |

Class decoding: **330 → 0, 40 → 1, 70 → 2, 154 → 3, 300 → 4**.
Other raw values produce `pd_class: null`. The observed 331 is retained as raw;
it is not declared to be a new class or a fault. In the limit field, raw 330
means Auto, not a fixed 33 W limit.

### `ports[].poe.recovery`

| Field | Type / unit | Meaning |
| --- | --- | --- |
| `enabled` | Boolean? | Currently null: per-port enable flag not reliably established |
| `ping_address` | string? | Configured target, up to 16 source bytes; empty string retained |
| `startup_delay_seconds` | integer?, s | Configured delay before monitoring |
| `interval_seconds` | integer?, s | Configured check interval |
| `failure_threshold` | integer? | Configured failed-check threshold |
| `break_seconds` | integer?, s | Configured power interruption duration |
| `failures_current` | integer? | Current failure counter |
| `reboots_raw` | integer? | Raw restart statistic |
| `pings_raw` | integer? | Raw check statistic |

The final three are read as signed16; negative values become null. Hardware wrap
and reset behavior are untested. Configuration presence does not prove the feature
is active or has restarted a device. JSON reads do not send pings or trigger recovery.

## `loop_prevention`

| Field | Type | Meaning |
| --- | --- | --- |
| `enabled` | Boolean? | Currently null: active mode not independently established |
| `rldp_mask_raw` | uint32? | Current software RLDP mask, RAM `0xbf00e280` |
| `rlpp_mask_raw` | uint32? | Current software RLPP mask, RAM `0xbf00e2a0` |
| `rlpp_self_mask_raw` | uint32? | RLPP self-loop mask, RAM `0xbf00e2a4` |

A zero mask does not prove absence of loops when detection is disabled. Masks
may expand LAG groups; do not assume every bit is a verified blocked front-panel
port. The endpoint reads existing masks without running loop diagnostics.

## Collection guidance

- Validate HTTP, JSON, schema version and the ordered 18-port list. Expose a
  collection error instead of replacing failed responses with zeros.
- Treat null as missing measurement, not zero/false.
- Compute rates using collector-side elapsed time: bit/s = `8 × Δbytes / Δseconds`.
  Raw uptime is not yet a suitable time base.
- A decreasing counter may mean reset or wrap. Do not publish negative rates;
  per-field wrap behavior still requires verification.
- Avoid double counting aggregates/categories and do not label provisional
  counters as standard IF-MIB without evidence.
- The early design's 15-second polling interval has not been stress-tested.
  Two manual responses do not establish a safe sustained collection interval.

A Prometheus exporter and Grafana dashboard are not included in this release.
This reference specifies the source behavior needed to develop them.

## Real examples and repeatable validation

[Sample 1](evidence/2026-10-17-switchlens/stats-01.json) and
[sample 2](evidence/2026-10-17-switchlens/stats-02.json) are real observations,
published at the owner's request. Unlike `examples/demo.synthetic.json`, they
contain this bench's real addresses and are not generic configuration templates.
Original messages, screenshots, hashes and evidence limits are in the
[test journal](evidence/2026-10-17-switchlens/README.md).

From the repository root with `requirements-dev.txt` installed:

```bash
python3 - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator
schema = json.loads(Path('schema/stats.schema.json').read_text())
validator = Draft202012Validator(schema)
for path in sorted(Path('docs/evidence/2026-10-17-switchlens').glob('stats-??.json')):
    data = json.loads(path.read_text())
    validator.validate(data)
    assert [p['port'] for p in data['ports']] == list(range(1, 19))
    for port in data['ports']:
        for value in port['counters'].values():
            assert value is None or 0 <= int(value) <= 2**64 - 1
    print(path.name, 'PASS', len(data['ports']), 'ports')
PY
```

Structure/range validation does not calibrate sensors. Remaining checks include
stock-UI comparison, loaded PoE, connector mapping, refresh timing, reset/wrap
behavior and extended operation.
