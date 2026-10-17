**English** | [Русский](COOLING-CONTROL.ru.md)

# Bounded cooling tests — v0.1.2

v0.1.2 adds `cool` commands and a read-only `cooling` object to `/stats.json`.
The owner has confirmed its CLI and GPIO27=0 readback during an active test;
automatic mode was also observed. No clear fan improvement was reported.
The v0.1.2 JSON hardware result is pending; v0.1.1 JSON is already verified.
[Download and checksums](../releases/v0.1.2-cooling/README.md).

## Owner's observations before this build

Noctua NF-A4x20 PWM, 12 V, four-pin fans with three standard wires connected;
the PWM wire is unconnected. The same fan fails to start in either header but
runs after a push. One fan runs and one remains stopped; FAN is orange.

Reported direction register: `0x39000000`; data register: `0x39780000`.
These give GPIO26 input/level 0 and GPIO27 output/level 1. Repeated data reads
were unchanged. A brief manual write of `0x31780000`, followed by restoration
to `0x39780000`, produced a tentative observation that one fan slowed down;
the other still did not start. This does **not** establish 0 = fast or 1 = slow.

A truncated `reg flashget 0x1` hung the old console. Long pasted input may have
lost bytes; hardware FIFO overflow is a hypothesis, not a verified diagnosis.
This build provides short commands and validates `reg` arguments. No new board
measurement is a prerequisite for the requested software test.

## Commands after installing this BIN

Enter one line at a time at `RTK#`, without copying the prompt:

| Command | Action |
| --- | --- |
| `cool status` | Print build ID, GPIO control/direction/data, GPIO26/27 levels, state, ticks and PoE sum |
| `cool test 0` | Hold GPIO27 at 0 for at most 100 raw timer ticks, then resume the stock controller |
| `cool test 1` | Same test with GPIO27 at 1 |
| `cool auto` | Cancel an active test and recompute the normal output from current PoE load |

Start with `cool status`, then test one level, observe both fans and FAN, and
check status again. Wait for `mode=auto` before the other test. `cool auto`
cancels early. `help` and `help cool` include the command. Blank-line repeat is
disabled for `cool`. Existing v0.1.1 does not contain these commands.

The limit is **100 raw IRQ ticks**, not a calibrated number of seconds. Expiry
is serviced by the UART poll even without keyboard input and by the normal
PoE/controller path. A stopped timer or blocked CPU/event loop can delay return;
this is a software timeout, not an independent hardware watchdog. If automatic
return cannot be confirmed, cancel with `cool auto`; if the console is stalled,
power-cycle rather than leaving an unknown test mode active. It is not saved to flash.

Only GPIO27's data bit is changed with the stock read/modify/write helper.
There is no per-fan selection, arbitrary voltage setting, PWM frequency setting,
RPM control, threshold modification or startup-boost policy in this release.
A second test is rejected while one is active, so it cannot extend the deadline.
An invalid state, non-GPIO mux or non-output direction rejects a new test.

## Implementation and timer state

The original controller at `0xbfc5c368` still aggregates PoE power. In auto mode
it retains the exact thresholds: sum <1460 gives level 1; sum >=1501 gives 0;
1460–1500 keeps the previous state. The raw unit is 0.1 W. These levels are
deliberately not named fan speed modes.

No new persistent SRAM is allocated. During a test the existing state word at
`0xbf014840` contains `0xd4000000 | saved_state<<25 | level<<24 | start_tick24`.
The tag mask is `0xfc000000`; normal values remain 0/1. The original controller's
other-state branch leaves the tag intact while continuing to update the PoE sum.
The hooked output function enforces the selected level. At expiry/cancellation
it restores the saved state and invokes the original controller, which evaluates
the **current** load before writing the output. Subtraction uses a 24-bit modular
tick difference, tested across both 24-bit and 32-bit wrap.

The image is pinned by SHA-256. The GPIO output entry, two CLI lookup calls and
UART polling call are patched in addition to the existing JSON/UART hooks.
The payload stays in audited FF padding; the linker rejects writable globals,
BSS and GOT/PLT. See [manifest](../releases/v0.1.2-cooling/build-manifest.json).

## JSON and register-command limits

`GET /stats.json` retains stock authentication and adds optional `cooling` under
schema version 1. Old v0.1.1 responses remain valid against the updated schema;
consumers using an older strict schema must update it to accept the new object.
The HTTP path only reads. It never expires/cancels a test or forces GPIO output.
[`cooling` field reference](JSON-API.md#cooling-v012).

`fan_rpm` and `fan_status` remain null. GPIO26 is a sampled input connected by
software to LED modes; it is not a verified per-fan tachometer or health result.
GPIO reads occur sequentially, not as an atomic hardware snapshot.

The `reg` wrapper checks argument count, complete unsigned numeric tokens,
32-bit overflow, four-byte alignment and address/count bounds. `soc*`, `9300*`
and ASIC offsets must fit 16 bits. `flashget/flashset` access SRAM despite their
names: this build limits them to offsets 0..`0x1fffc` and `flashget` to at most
64 words (0 means one word in the stock command). During a cooling test `reg`
writes are rejected. Other stock commands are not made read-only by this wrapper.

This cannot detect dropped digits that still form a valid aligned address, and
does not make every valid register access harmless. In particular the truncated
`0x350` is still syntactically valid. Prefer the short `cool` commands for this test.

## Checks and remaining hardware work

24 MIPS tests pass: 10 cooling/CLI tests, 10 HTTP/JSON tests and 4 scheduler/boot
path tests. They cover both levels, hysteresis boundaries, timer wrap, idle
expiry, explicit cancellation, unrelated GPIO-bit preservation, malformed `reg`,
authenticated/read-only JSON, CRC acceptance/rejection and shared CLI/HTTP RAM.
Host serializer/MIB checks and ASan/UBSan pass; LeakSanitizer was disabled because
the execution environment uses ptrace. [Reports](../releases/v0.1.2-cooling/README.md).

The owner later confirmed an active test with data `0x31780000`, GPIO27=0,
and 100 remaining ticks; separate automatic-mode output showed `0x39780000`.
There was no clear fan effect or confirmed start of the second fan. This does
not establish a voltage/speed mapping. Do not repeat the same read as an
uncompleted prerequisite. Individual RPM still requires a verified tach source
and time base. [Further code analysis and GPIO26 options](../research/COOLING-PATHS.md).
