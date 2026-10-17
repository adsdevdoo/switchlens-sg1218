**English** | [Русский](IMPLEMENTATION.ru.md)

# Host serializer and MIB reader

Reader edition of the16 October2026 host-prototype report.
[Original historical text](IMPLEMENTATION.txt). The later MIPS adapter and working
hardware firmware are documented in [FIRMWARE](FIRMWARE.md) and the
[test journal](evidence/2026-10-17-switchlens/README.md). Earlier “no firmware
built” statements describe the prototype date only.

## Implemented host layer

`sg_stats.c`, `sg_stats.h` and serializer tests implement the full schema:
system, global PoE,18 ports, counters, per-port PoE/Recovery and loop fields.
All seven System Info values are included; name aliases description.
A128-byte output buffer streams fragments without holding the full document;
this is not total stack usage. uint64 uses exact decimal strings; power/voltage
can use integer tenths without printf/floating point. UTF-8 is checked, strings
escaped and source byte lengths bounded more strictly than schema character counts.

Source errors/invalid types/ranges become null with separate sg_result error
counts. Unknown values are never invented zeros. rx_discards and TX256–511
are forced null without invoking a source. Partial writes retry only with positive
progress; zero/error aborts immediately, and final flush is checked.

MIB reader accepts a read32 callback, with no direct MMIO writes/network/device
execution in the host layer. It allowlists41 single-register selectors plus
two-word1/9; rejects no-op, unsupported, stock sums and defective58. Ports1–16
map toASIC0–15,17/18→24/25, following file4dc3c. Panel mapping still needs testing.
Base is1200+physical*100; offsets match mib-map.json. High–low–high retries at most
three times and leaves caller output unchanged on failure. Latching, clear-on-read,
actual width and parallel-reader effects are not established. Widening to uint64
does not recover missed wraps; separate registers are not atomic snapshots.

## Build/check

C99 compiler, make, Python3/jsonschema are required:

```bash
python3 -m pip install jsonschema
python3 tools/generate_fields.py
make test
./build/fixture > demo.synthetic.json
ASAN_OPTIONS=detect_leaks=0 make BUILD=build-sanitize \
  CFLAGS='-std=c99 -Wall -Wextra -Werror -O1 -g' \
  SANITIZE='-fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie' test
```

Fixture data uses synthetic192.0.2.x addresses and sends no commands to a switch.
It does not establish availability of all hardware fields. Host build binaries
are not tracked. LeakSanitizer failed under ptrace in the preparation environment,
so only leak detection was disabled; ASan/UBSan stayed active. This does not test
hardware leaks. sg_stats/sg_mib perform no dynamic allocation.
[Original successful test output](host-test-results.txt).

## Adapter contract

`sg_source.begin` obtains a small scope snapshot; get supplies fields; has_poe
must determine applicability. Failure to determine applicability aborts the response.
Different ports are sequential. Do not disable interrupts for the entire HTTP
response or call configuration/reset/loop-protection handlers. Copy bounded
RAM strings with lifetime through the next get; name/description share one snapshot.

`sg_sink.write` must return positive bytes accepted, not the stock emit's status0.
Do not assign a stock send address directly. Callbacks are synchronous/bounded;
recursive use of the global HTTP buffer is unsupported. Stop on error; the client
accepts only complete JSON. finish checks the transport's final flush.

## Exact-image bindings

Input SHA-256 `c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
Audit with `python3 tools/audit.py /path/image.bin` before transformation.
MIB BFC27FB8→BFC1D930/file15930; helper BFC1D7F0 hides read failure; low read
BFC10768/file8768 preserves status. HTTP raw BF01CAC0/file66f8 returns0/−1;
stock printf/end hide errors. System/PoE/loop sources are in research reports.
Uptime BF002E90 has unconfirmed seconds scale, conditional on LXB200MHz.

The initial report left MIPS/linker/stack/router/live adapters/deadline work open.
Those implementation steps and tests were subsequently completed; actual maximum
stack/IRQ usage, PoE freshness, sustained polling and restoration remain separate
hardware concerns. No flash JSON file or background writes are introduced, and
stock authentication is retained.
