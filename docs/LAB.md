**English** | [Русский](LAB.ru.md)

# Bench status — 17 October 2026

The owner performs all hardware actions on one switch that is not yet deployed.
**Working firmware:** v0.1.1 boots after stock web upgrade, accepts UART `help`
and returns two valid, changing JSON replies. [Full evidence](evidence/2026-10-17-switchlens/README.md).

| Fact | Source and scope |
| --- | --- |
| PCB 2060500612, Ver:5.40 | Owner photographs; external/reported UI hardware version V5.0 |
| U6 GD25Q16BSIG | [Chip photograph](images/uart/flash-marking.jpeg) |
| 16 Mbit / 2 MiB, 2.7–3.6 V, SOP8 208mil | [GD25Q16B datasheet](datasheets/GD25Q16B_Datasheet_2.3.pdf), PDF pp. 4 and 41; specification, not a board measurement |
| Original SPI export | [Stored file and byte analysis](../backups/original/2026-10-17/README.md) |
| Programmer verification and resoldering | Reported by owner; no second independent read file supplied; stock web worked afterward |
| R41/R42 | Owner traced series gaps and populated both with 0 Ω 0402; factory nominal value unknown |
| J2 pin 1 TX | Readable output and owner's identified contact |
| J2 pin 2 RX | Owner-described wiring; help confirms bidirectional exchange, no new wiring photograph |
| Serial settings | CP2102, COM3, 38400 baud, 8N1, Flow None |
| Modified-runtime boot | Web upgrade, SignCheck Pass, RTK# and code init observed |
| JSON | Both samples validate; all 18 ports; uptime and counters change |

J2 numbers follow the owner's measurements, not an assumed image orientation.
Pin 3 GND and pin 4 3.3 V are based on the owner's checks. The flash chip pinout
is separate from J2: [datasheets](datasheets/README.md#u6-gd25q16bsig).
[Earlier stock evidence](evidence/2026-10-17/README.md), [vendor images](../vendor/tp-link/tl-sg1218mpe-v5/README.md).

## UART connection

1. Disconnect switch power and USB-UART before soldering or rewiring. On another
   board verify traces and ground before populating empty resistor sites.
2. Connect common GND and switch J2 pin 1 TX to adapter RXD. For command input,
   the described bench connects pin 2 RX to compatible-level adapter TXD.
   Do not connect adapter VCC/3V3/5V to the switch. A 3.3 V selector position
   alone does not measure the adapter's TXD logic level.
3. Close PuTTY before using the receive-only capture script. Defaults: COM3,
   38400 8N1, 60 seconds; power up after LISTENING. [Capture guide](UART-CAPTURE.md).

## Why stock Enter was silent

[Static analysis](../research/UART-CONSOLE.md) found bit 0 at `0xbfcff018` cleared;
the periodic dispatcher skips UART CLI input. Thus silence did not test RX soldering.
v0.1.1 enables the dispatcher and command permissions with two instructions.
The owner then obtained RTK# and help on hardware. This is runtime CLI, not a
confirmed bootloader recovery interface.

## Next checks

Compare JSON against stock UI and a real PoE consumer; check physical port mapping,
settings and discard behavior; calibrate raw uptime against external time; test
polling under traffic, disconnected/slow clients and extended operation.

Recovery has not been verified. The owner declined another desoldering exercise
as a prerequisite; do not reintroduce that requirement. The Xgpro export has a
272-byte trailer beyond the 2 MiB array. An update BIN is not a full flash dump.
No working UART/TFTP recovery commands have been established.

The supply contains mains voltage; work on its primary side is not required.
This test session was explicitly authorized for publication; future sessions are
not published automatically.
