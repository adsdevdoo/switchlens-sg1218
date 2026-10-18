**English** | [Русский](FIRMWARE.ru.md)

# SwitchLens implementation

## v0.1.6 update (18 October 2026)

Built on the v0.1.5 hardened base. Exact raw `GET /stats.json` bypasses the outer
IP/cookie/expiry path without changing session state; all other requests replay
the stock prologue and authentication. See [HTTP trace and checks](HTTP-AUTH.md).
TDDP/TSDP initialization and callbacks remain disabled. UART/cooling and JSON
schema/metric code remain in place. **Hardware installation is unconfirmed.**

Build: `python3 tools/build_firmware.py ORIGINAL.bin --uart-cli --cooling-cli --anonymous-stats --output build-v016`.
The released artifact uses GCC 12.4.0 (Ubuntu 12.4.0-2ubuntu1~24.04), binutils 2.42;
exact flags/source hashes are in the [manifest](../releases/v0.1.6/build-manifest.json).
Earlier toolchain/version observations below describe their named builds.


**Working firmware, updated 17 October 2026:** v0.1.1 completed stock web
installation and runtime boot; UART help and two complete changing JSON replies
were observed on the owner's unit. [Evidence](evidence/2026-10-17-switchlens/README.md),
[JSON reference](JSON-API.md). Remaining hardware checks are listed separately.

The implementation targets exactly TP-Link TL-SG1218MPE(UN) V5.0 official
`1.0.0 Build 20230616 Rel.57668`. The builder rejects any other input hash:

```text
c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32
```

The earlier v0.1.0 archive contains the base JSON payload. Historical v0.1.1 adds
two UART instructions and CRC, with the same payload. Historical filenames,
manifest labels and the HTTP `experimental-1` marker remain unchanged for
identity/reproducibility; they are not the current hardware-test status.

## Implemented behavior

- Exact dynamic `GET /stats.json` in the stock HTTP server; v0.1.6 adds the narrow anonymous path,
  application/json, no-store and stock connection-close behavior.
- System Info plus name/description alias; 18 ports, link/speed/duplex/flow control,
  a 49-counter structure, global/per-port PoE and Auto Recovery information.
- Streaming serializer with 128-byte fragments, bounded text and strict UTF-8,
  JSON escaping, decimal uint64 strings, checked source/sink errors.
- Read-only adapter: no configuration setters, PoE commands, MIB resets or flash writes.
- No malloc, new task or mutable global RAM/BSS/GOT for the payload.
- Raw loop masks; unconfirmed fields explicitly null.

`uptime_seconds`, `lag_id`, measurement validity, extend flag, per-port recovery
enable, loop enable and general RX discards have no confirmed implementation.
TX 256–511 bucket is deliberately excluded because stock selector 58 leaves the
low output word unwritten. Raw uptime is available without a time-unit claim.

The UART CLI is the stock runtime interface and includes write/reset commands;
only the telemetry endpoint is read-only. Initial help is verified; other CLI
commands and bootloader recovery are not implied.

## Addresses and evidence

All offsets include the 16-byte update header; ranges are half-open.

| Area | Established implementation/evidence |
| --- | --- |
| Runtime mapping | Normal flash VA `0xbfc08000 + file offset`; RAM code `[0x3160,0x8178)` → `BF019528..BF01E540`, initial SP `BF01F800` |
| Payload placement | FF region starting file `0xD8640`, VA `BFCE0640`; section sizes/headroom in manifest; writable/BSS/GOT forbidden by linker and ELF checks |
| HTTP hook | File `0x3425C` replaces jal strcmp, `0x34280` changes statistics branch; delay slots and o32 saved registers retained |
| Session/router | `BFC3B740` checks GET/session before route; invalid session uses `BFC3FC18`; outer entry `BFC3CE48` has a v0.1.6 exact-GET trampoline; fallback resumes at `BFC3CE50` |
| HTTP helpers | Init `BFC3B278`, status `BF01CD38`, header `BF01CC5C`, raw `BF01CAC0` |
| HTTP buffer | `BF010F8C..BF011540`, 1460 bytes, reused stock buffer |
| Formatter registration | File `0x302AC..0x302F8` and `0x2B840`; emulator uses corresponding pointers at `BF00ECCC` |
| ASIC reads | `BFC10768` propagates callback errors; adapter avoids stock wrappers that hide them |
| MAC | ASIC offsets `A9EC/A9F0`; stock getter `BFC1F854` |
| IPv4 | Network-order bytes from `BF016D3A/3E/42`; stock formatter `BFC3147C` |
| PoE | Cache base `BF0143E0`, records `BF014408 + 48*i` |
| Port config/status | Getters `BFC532DC`, `BFC533CC`; live path `BFC27C30`; MIB mapping in research/mib-map.json |
| Recovery | RAM `BF002110` or flash `B41FEB1C`, record start +8, stride 40; stats `BF014774 + 6*i`; handler file `0x3AE90` |
| CRC | Big-endian CRC32 at file 0, covers `[0x10,0xF7000)`; image length and tail retained |
| UART addition | File `0x25e94`: `8c45f018` → `24051fff`; `0x25ed8`: `30420001` → `24020001` |

[Platform analysis](../research/PLATFORM-FOLLOWUP.md), [MIB map](../research/mib-map.json),
[metric sources](../research/metric-sources.json), [UART analysis](../research/UART-CONSOLE.md).

Most individual MIB categories read 32-bit words. Byte totals use bounded
high–low–high reads. RX/TX good-packet aggregates add unicast, multicast and
broadcast values. `tx_bad_packets` uses selector 21 (also excessive collisions).
RX bad-packet aggregation preserves the stock formula, including TX categories
and 32-bit subtotal wrap: selectors 37 + 34 + 43 + 40 + 31. This preserves UI
behavior, not standard IF-MIB semantics. See the [exact formula](JSON-API.md).

PoE reads existing cache. Nonpositive per-port measurements are null following
the UI's unavailable display. Unknown status retains its numeric code with null
text; remaining power is clamped only at zero, while original consumption is
not clamped to budget. Cache age and cross-port atomicity are unknown.

## Reproducible build

Verified toolchain: GCC `13.2.0-23ubuntu4cross1`, binutils `2.42-2ubuntu1cross5`,
big-endian MIPS32r2, o32, soft-float, `-G0`, no-abicalls.
[Package versions/hashes](../research/toolchain-packages.json) were checked
against Ubuntu noble package metadata. External addresses are in
`target/firmware.ld`; no libc/libgcc is linked. Decimal uint64 conversion avoids
64-bit division helpers.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
make test
python3 tools/build_firmware.py /path/to/official.bin \
  --cc mips-linux-gnu-gcc-13 --prefix mips-linux-gnu- --uart-cli
python3 tests/test_target.py /path/to/official.bin --build build-target \
  --synthetic-output build-target/emulator.synthetic.json
```

Without `--uart-cli`, the builder preserves stock CLI-off behavior. To reproduce
the published UART package from its archived payload without recompiling it:

```bash
python3 tools/build_uart_diagnostic.py
python3 tests/test_uart_console.py
python3 tests/test_release_paths.py
```

The official input is archived in [vendor/tp-link](../vendor/tp-link/tl-sg1218mpe-v5/README.md).
Output includes BIN, manifest, payload, ELF, linker map, stack-usage files and
results. Manifest records output hashes, CRC and source hashes. Two builds in
separate directories were byte-identical with the saved toolchain; other
compilers are not promised identical bytes. Scripts do not flash devices.

## Emulator coverage and limits

Tests execute the built MIPS payload and stock router, HTTP formatting/header/raw,
strcmp/memcpy and MMIO-read path. Socket send is replaced with collected bytes
or errors; RAM/MMIO data is synthetic. Stock statistics/login handlers are
intercepted at entry, not fully exercised as HTML flows. CPU model 24KF is not a
model of the whole switch.

Checks include complete JSON/schema/System Info/18 ports/PoE, uint64 maximum,
MIB read errors and unstable high words, both config locations, unknown PoE,
session/POST/similar URLs, saved registers/SP, first/intermediate/final send
errors, raw deadline, stack guard, hashes/CRC and allowed binary changes.

Emulator MMIO, flash and request memory are write-protected. Before/after SRAM
snapshots permit only stack and stock HTTP-buffer ranges. This is not a trace of
every intermediate write: Unicorn 2.1.4 MEM_WRITE hooks caused a false CPU exception
on a branch-delay-slot store and were not used for that purpose.

One synthetic case produced 37,194 HTTP bytes in 26 sends and used 840 bytes of
observed stack from entry SP. The pre-handler guard requires 3072 address-space
bytes above RAM code. These figures do not establish stack safety under real IRQs
and TCP load. A 40-raw-fast-tick budget is checked between operations, but cannot
interrupt a hanging stock call. Outer `BFC3CE48` hides router return status;
clients must reject truncated JSON and HTML login responses.

Six UART tests, ten HTTP/JSON tests and four scheduler/shared-RAM/boot-path tests
passed. Host serializer/MIB and ASan/UBSan passed with LeakSanitizer disabled.
[Final review](FINAL-CHECK.md). Hardware CPU/RAM usage, long-term leaks, latency
and multi-client stress have not been measured. Delivery of two complete JSON
responses has now been observed on the actual unit.

## Hardware observations and next checks

[Bench](LAB.md) and [test journal](evidence/2026-10-17-switchlens/README.md) establish
web install, boot, SignCheck Pass, UART help and dynamic JSON. The original dump
is retained; the owner declined repeat desoldering as a preliminary restore test.
Recovery remains unverified. An update BIN is not a raw full-flash image.

Next compare System Info, PoE/Recovery, four stock counters and configured modes
against the UI; verify physical port mapping, known traffic, wrap/reset and
read behavior. Measure uptime scale externally. Test real PD loads, slow or
interrupted clients, simultaneous users and sustained operation. A possible
rollback/recovery route must be evaluated separately; runtime CLI does not prove
bootloader recovery commands. Future logs require their own publication scope.
