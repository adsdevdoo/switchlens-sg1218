**English** | [Русский](GPIO-INVENTORY.ru.md)

# GPIO inventory and the limits of the cooling search

17 October 2026. **The earlier search was not an audit of every GPIO path.**
It covered 23 direct references to the main SoC data writer and the PoE/cooling
callers. This extension covers input and direction helpers, direct MMIO setup,
default board configuration, the external GPIO driver and a resolved indirect
callback path. No additional fan-speed command was identified in these paths.
This is still not a proof that every computed path in the firmware is resolved.

Source: stock June 2023 BIN, SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
No device was accessed or firmware changed. See [reproducible evidence](gpio-inventory-evidence.json)
and the [previous cooling investigation](COOLING-PATHS.md).

## All 32 bits in the supplied snapshot

The owner previously supplied `cnr=0xc2e7ff00`, `dir=0x39000000`,
`data=0x39780000`. These are register bit indices, not connector pin numbers.
Here “GPIO” means a cleared CNR bit, following the stock helper's operation.
“Alternate” means the CNR bit is set; the exact alternate function is not
established by that bit alone. Direction bits do not establish direction in an
alternate function. This is one historical snapshot, not a new measurement.

| GPIO bit(s) | Snapshot selection | Code relationship found |
| --- | --- | --- |
| 0–7 | GPIO input | No fixed-pin caller identified in the reviewed paths |
| 8–18 | Alternate | Generic configured-input path accepts 8–31; disabled in the stock default configuration |
| 19 | GPIO input | Selects copper/fiber for internal port 25 |
| 20 | GPIO input | Selects copper/fiber for internal port 24 |
| 21 | Alternate | Data reader used by the configuration-reset/button handler |
| 22 | Alternate | Reset/watchdog path later selects GPIO output and writes 0 |
| 23 | Alternate | No fixed-pin caller identified |
| 24 | GPIO output | Set high during startup; low/high pulse during PoE initialization |
| 25 | Alternate | Optional board-mode input starts at `25 + configured_offset`; disabled in the default configuration |
| 26 | GPIO input | Selects two indicator LED modes; not part of the PoE-load output decision |
| 27 | GPIO output | Binary output controlled by PoE-load hysteresis; v0.1.2 can temporarily override it |
| 28 | GPIO output | Clock of the software PoE-device bus |
| 29 | GPIO output | Data of that bus; transactions also change its direction |
| 30–31 | Alternate | No fixed-pin caller identified |

“No fixed-pin caller identified” does not mean an unconnected or safe spare pin.
Generic helpers can accept a pin number dynamically. Snapshot direction also
does not describe every instant of a bus transaction or a later reset path.

## Additional direct register access

`0xbfc101c0` (file `0x81c0..0x8270`) directly clears bits 19 and 20 in
`0xb8003500` and `0xb8003508`. It configures both as GPIO inputs and does not
write GPIO data. Three executions with different initial register words verified
that all other GPIO bits and the data word are preserved. Its switch-register
writes also execute against synthetic MMIO; no calls are mocked in these cases.
The earlier cooling audit explicitly mocked this helper and did not establish
its contents.

`0xbfc29254` reads GPIO20 for index 0 and GPIO19 for index 1. Its branches use
the stock strings `set port %d to fiber mode` and `set port %d to copper mode`.
The owner log's PHY value `0xc984` selects board ID `0x43` in `0xbfc2eba8`.
Executing the original media poll `0xbfc293c8` with that selection and the
supplied data word yields internal ports **24/25 copper, 26/27 fiber**, matching
the boot log. Port setters are mocked; this verifies the CPU decision, not
physical links. Internal port IDs are not front-panel port numbers.

GPIO21's reader at `0xbfc51080` counts low samples. On the fifth low sample it
calls `0xbfc51f48`, identified by the stock diagnostic string
`sal_flash_cfg_reset`, then the system reset wrapper. It is not a fan tachometer
counter. GPIO22's output is in the separate reset/watchdog routine.

## External GPIO and the indirect call missed by a direct-only search

The stock binary includes names `dal_maple_rtl8231_init`,
`dal_maple_extGpio_pin_data_set` and corresponding input/direction functions.
These identify the software driver; they do not confirm which physical chip is
populated on this PCB.

For board ID `0x43`, `0xbfc29550` enables external device 0 and uses the table at
RAM `0xbf0008f0` to configure these inputs:

| Internal port | External GPIO input pair |
| --- | --- |
| 24 | 8, 9 |
| 25 | 3, 4 |
| 26 | 24, 25 |
| 27 | 13, 14 |

Original enable/direction routines were executed with mocked low-level register
transport: 38 read/write transactions, writes to registers 0, 2, 3, 4, 5 and 6.
This initialization does not write the driver's output-data registers. It does
not prove that the physical external device acknowledged these operations.

**An external GPIO data writer does have a constructed callback reference.**
At file `0x20fd4`, code constructs `0xbfc24588`, passes it to callback setup
`0xbfc11590`, and stores it in the callback structure at `0xbf016ac8 + 0x14`.
The software serial-bus routines then call it with `jalr`. Thus “no direct
callers” alone would have missed a real output path.

The resolved consumer is optical-module media/speed handling in `0xbfc28da4`:
it reads address `0x50`, offsets 12 and 11, and uses the diagnostic string
`pOpticalConf[%d].media_speed=%s speed=%s`. The associated per-port clock/data
table is at RAM `0xbf000980`. These external GPIO numbers are a separate
namespace from the SoC GPIO numbers above. The board-ID `0x43` poll follows the
internal-GPIO branch; the emulator confirms it does not call this external
optical-module poll. No fan-specific consumer was identified in this path.

## Configuration-dependent paths

The default board configuration at update file `0xf7000..0xf764c` is loaded from
flash address `0xb40ff000`. The archived original SPI export contains identical
bytes at `0xff000..0xff64c`. Executing the stock configuration loader confirms:

- Configured four-input feature at offset `0x1a8` is disabled; its four pin
  entries are sentinel `0x89`.
- Optional input feature at `0x4e4` is disabled; its pin offset at `0x4e8` is 0.
- All six generic masked-register initialization rows beginning at `0x4fc`
  are disabled. This path can otherwise perform computed SoC register writes.

These are default/archived values, not a readback of the current runtime's RAM.
They must not be used to claim that arbitrary register-write paths cannot exist.

## Search coverage and conclusion

The scan inventories 7 direct mux references, 17 direction references, 23 data
writer references and 6 reader references to the main SoC helpers. Eight
alternate SoC helpers have no direct references, aligned literal pointers or
matching nearby LUI-plus-ADDIU/ORI construction candidates in this scan. The
scan includes startup, RAM-copied code and the specified runtime intervals;
full-image aligned literal searches include data tables. Candidate pairs are
syntactic and may include false positives; resolved uses are described above.

GPIO27 remains the identified binary cooling-output candidate; GPIO26 is the
indicator input. No additional PWM duty setting, RPM target, per-fan output or
stall-retry routine was identified by this extension. The physical relationship
between GPIO27 and the fan headers remains unconfirmed. A complete mapping of
all pins and every possible computed path has **not** been established.

Reproduce with `requirements-dev.txt` installed:

```bash
python3 tools/audit_gpio_inventory.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin > research/gpio-inventory-evidence.json
```

The evidence includes all 32 decoded snapshot bits, image/block hashes, helper
references, constructed-reference candidates, explicit mocks, configuration
fields and external-register transactions.
