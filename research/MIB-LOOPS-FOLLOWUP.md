**English** | [Русский](MIB-LOOPS-FOLLOWUP.ru.md)

# Additional MIB counters and loop masks

Static analysis16 October2026 of SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
[Original record](MIB-LOOPS-FOLLOWUP.txt). Current firmware is working;
additional counter meanings remain provisional despite successful JSON output.

## Sources and addressing

The126-selector jump table is file93250; getter15930:15cf0.
OpenWrt [2025 register names](https://lists.infradead.org/pipermail/lede-commits/2025-July/026486.html),
commit831c1cd864af6895270fb598185f2d04b3936401, rtldsa_838x_mib_list, and
[2020 read path](https://lists.infradead.org/pipermail/lede-commits/2020-September/007884.html)
provide family comparison. Address formula is base+(port<<8)+252−descriptor.offset;
for two-word values high is four bytes before low.
The source [dsa.c](https://raw.githubusercontent.com/openwrt/openwrt/openwrt-24.10/target/linux/realtek/files-6.6/drivers/net/dsa/rtl83xx/dsa.c)
hash is retained in mib-map.json. This is an external family map, not this board's
source. Address matches support proposed names, not exact die identity, physical
width, reset behavior or OpenWrt image compatibility.

Offsets below are within `0x1200+(physical_port<<8)`:

| Field | Selector | Offset |
| --- | ---: | --- |
| rx_bridge_discards | 125 | +10 |
| rx_mac_discards | 84 | +bc |
| rx_undersize_drops | 65 | +6c |
| rx_crc_align_errors | 31 | +60 |
| symbol_errors | 22 | +44 |
| rx_unknown_control_opcodes | 23 | +48 |
| rx_pause_frames | 24 | +4c |
| tx_pause_frames | 25 | +50 |
| drop_events | 26 | +54 |
| rx_undersize_packets | 35 | +68 |
| tx_undersize_packets | 36 | +64 |
| rx_oversize_packets | 38 | +74 |
| tx_oversize_packets | 39 | +70 |
| rx_fragments | 40 | +78 |
| rx_jabbers | 43 | +7c |
| collisions | 46 | +80 |
| tx_single_collision_frames | 17 | +30 |
| tx_multiple_collision_frames | 18 | +34 |
| tx_deferred_transmissions | 19 | +38 |
| tx_late_collisions | 20 | +3c |
| tx_excessive_collisions | 21 | +40 |

Size category RX/TX selectors:64=48/49,65–127=51/52,128–255=54/55,
256–511=57/58,512–1023=60/61,1024–1518=63/64,1519–max=66/67.
Selector58 is excluded. Individual categories are32-bit reads; decimal uint64
format does not extend hardware. Size ranges are not cumulative histogram buckets.
Do not add overlapping drops/errors into an invented total. General rx_discards
stays null because a sum equivalent to ifInDiscards is unproven. Stock TxBadPkt
uses21, the proposed excessive-collision counter, not all transmit errors.

## Getter pitfalls

- 68 selectors jump to BFC1D9E0 and return0 without touching output. Success
  status alone does not establish support.
- Selector58→file15c30 reads +9c into stack+20, writes only high=0 to output,
  then returns without low. Keep tx_packets_256_511 null until an independent
  backend is verified; do not derive it by subtracting asynchronous totals.
- Ten selectors add two32-bit registers with addu and lose carry. Own64-bit
  addition preserves software carry but cannot make hardware counters wider
  or sampling atomic. Stock aggregate compatibility is documented separately.
- Helper BFC1D7F0/file157f0 overwrites BFC10768's status with zero. The adapter
  uses the lower error-propagating read path.
- Studied getter branches have no MMIO writes; that does not prove absence of
  hardware read side effects. Latch/reset behavior needs device testing.
- Stock two-word selectors1/9 have no high-word recheck. Current reader uses
  bounded high–low–high retries, which still needs hardware semantics validation.

## Loop masks

RLDP current BF00E280, previous BF00E284, file21f48:21fc8.
RLPP current BF00E2A0/self BF00E2A4, previous BF00E2A8/BF00E2AC,
file231d0:23298. Update2293c:22a18 uses BFC28250→BFC1FC18, starting at1<<port
but potentially replacing it with a group mask from registers3e00+4*i.
Consumers47f34:47f48 test bits after logical/physical mapping;48050:480c4 includes
port-state setters.

Read the globals only; do not run a detection tick to refresh JSON. A zero mask
with protection disabled does not prove no loop. LAG expansion and exact
loop/self-loop/blocked meanings require separate checks. They are not yet
verified per-panel-port blocking indicators.

## Reproduce

```bash
python3 tools/audit_mib.py firmware.bin openwrt-dsa.c > mib-map.local.json
```

The hash-pinned tool traces selected branches with synthetic register reads;
it is not ASIC emulation. Without the reference file, external names are omitted
but read paths remain available. Classification:68 no-op,45 low-word,2 two-word,
10 sums,1 incomplete-output. Full disassembly files referenced in the original
report can be regenerated and are not tracked. [Current field reference](../docs/JSON-API.md).
