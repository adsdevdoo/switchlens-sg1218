**English** | [Русский](JSON-CONTRACT.ru.md)

# JSON contract decisions and collection semantics

Reader edition of the16 October2026 design record. [Original](JSON-CONTRACT.txt).
Current authoritative structure: [schema](../schema/stats.schema.json);
complete working-firmware field descriptions: [JSON API](../docs/JSON-API.md).
Two actual responses are [archived](../docs/evidence/2026-10-17-switchlens/README.md).

One dynamic read-only GET returns application/json/no-store for system,18 ports,
PoE and loop masks. No flash file, counter reset, port/PoE mutation or new task.
Stock session authentication is retained. A proposed15-second polling interval
must still be validated under real load.

## Core rules

All structural fields are required; unknown/unavailable values remain null, not
fabricated zeroes. Counter values are unsigned decimal strings preserving uint64
precision. Many hardware categories are only32-bit. Distinguish absence of PoE
(`poe:null`) from supported PoE with unavailable measurements. Preserve raw status
and class codes; unknown text/class decoding stays null. Empty string differs
from null. Name aliases description; model is independent of editable description.
Version strings are preserved in full.

Source string bounds are bytes, not schema character limits; quote/backslash/
control escaping and UTF-8 validation are required. No full JSON/port-array stack
allocation; fixed fragments and checked partial/final writes. Snapshot is sequential,
not globally atomic. Do not disable interrupts throughout HTTP collection.
A client accepts only complete expected-schema JSON, not login HTML.

Global PoE exposes budget, consumption, remaining, raw consumption and recovery
enable. Consumption is not silently clipped to budget. Per-port PoE keeps
configuration separate from active status; raw/decoded class, priority, fixed/auto
limit, measurements and recovery have distinct semantics. Zero per-port readings
follow stock unavailable display. Measurement freshness is not claimed.

Reserved/unconfirmed values: uptime_seconds, lag_id, rx_discards, measurement
validity, extend flag, per-port recovery enable and loop enable. TX256–511 is
strictly null due defective selector58. Raw uptime is uint32 at BF002E90 with
unconfirmed time unit and possible wrap. Zero loop mask does not prove no loop.

## Auto Recovery

Stock help says Failures resets on successful ping/PD restart (fileba452),
and Reboots/Total Pings reset at9999 or switch restart (ba5af,ba6be). Exact boundary
and reset code were not independently tested. Consequently failures_current,
reboots_raw and pings_raw are gauges/raw observations, not promised monotonic
Prometheus counters. Do not apply rate to failures_current. They describe the
switch's mechanism, not all pings/reboots on a downstream Raspberry Pi. Do not
enable Auto Recovery merely to populate these fields.

## Collector-side calculations

- Traffic bit/s =8×delta(bytes)/collector elapsed seconds; handle reset/wrap/link
  speed changes and missing samples without negative or huge artificial spikes.
- Compute RX and TX utilization separately against actual speed; do not add both
  as one full-duplex percentage.
- Broadcast/multicast fractions use corresponding deltas over unicast+multicast+
  broadcast deltas; zero denominator means unavailable.
- PoE budget utilization is consumption/budget only when budget>0.
- Energy can be an approximate integration of valid power readings; missing
  intervals are not zero energy, and observation coverage should be reported.
- Link/PoE transitions are only observed changes between polls, not a complete
  hardware event log.

No confirmed sources exist for temperature, fan RPM, CPU/RAM utilization, SFP DOM
or reboot reason; they are not advertised as available metrics. Do not run Cable
Test from the endpoint: a result's existence does not establish passive acquisition.

Additional35 MIB fields comprise21 diagnostic categories and14 size intervals.
Register paths are statically established; names/width/side effects require
hardware checks. Size categories are separate ranges, not cumulative buckets.
No arbitrary sum of overlapping discards into IF-MIB totals. Raw RLDP/RLPP/self
masks may include LAG expansion and are not verified port-block states.

Later implementation provides the endpoint and hardware replies. Earlier wording
that it was only a proposed endpoint describes the design date, not current status.
