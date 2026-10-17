**English** | [Русский](UART-CAPTURE.ru.md)

# Receive-only UART capture on Windows

`tools/uart-capture.ps1` receives serial data, displays it and saves original bytes.
Defaults: COM3, 38400 baud, 8N1, no flow control, 60 seconds. It sends no UART data.

## Start

1. Close PuTTY and other applications using this port.
2. Remove any RXD–TXD jumper left from adapter loopback testing.
3. With the bench powered off, connect verified common GND and adapter RXD to
   owner-numbered J2 pin 1 (switch TX). R41/R42 on the tested board are 0 Ω 0402.
   Verify traces/ground on other boards; image orientation is not a pin-number rule.
   Leave adapter TXD/VCC/5V/3V3 unconnected for this receive-only procedure.
4. Double-click `tools/start-uart.cmd`; in the old standalone UART ZIP it was
   at the extracted folder root.
5. Wait for LISTENING, then power up. Capture ends after 60 seconds by default.
6. The latest folder is under uart-logs next to the script. Sharing it is manual;
   the script does not upload files.

From the script directory in PowerShell:

```powershell
.\start-uart.cmd -Port COM3 -Baud 38400 -Seconds 120
.\start-uart.cmd -OutputDirectory "$PWD\uart-logs"
```

Each run creates a new directory. Default path is calculated in the script body,
falling back to the current filesystem directory if necessary. Explicit output
path also avoids the original `Join-Path ... Path ... empty string` issue,
observed before COM opening on 17 October. The fix removed Join-Path from the
parameter's default expression. CMD's ExecutionPolicy Bypass applies only to its
PowerShell process, not system policy; organizational policy may still restrict it.

## Output files

| File | Meaning |
| --- | --- |
| `rx.bin` | Bytes returned by the COM driver without decoding |
| `rx.txt` | Printable ASCII, newlines and tabs; other bytes shown as `\xNN` |
| `rx.hex.txt` | Same bytes with offsets and host chunk-processing times, not individual bit timing |
| `session.json` | Settings, byte count, duration, completion and error state |

NO DATA means no bytes arrived during that observation; it does not establish
pinout, baud rate or absence of UART. Unreadable output remains useful because
raw bytes are saved. Port-open errors record `port_opened: false`.

No Enter, break, bootloader commands or test strings are sent. DTR/RTS are disabled
in software and should not be wired. Ctrl+C runs cleanup; forced termination or
closing the window may prevent final JSON metadata, while received BIN/TXT/HEX
chunks are flushed after each processing cycle.

## Established observations

- Owner's 17 October screenshot shows COM3/115200 loopback sending and receiving
  UART123, PASS. This tests the adapter loop, not the switch baud rate.
- Owner traced/populated R41/R42, 0 Ω 0402, and identified pin 1 as switch TX.
- Readable PuTTY boot and owner report establish 38400/8N1/Flow None.
  [Stock evidence](evidence/2026-10-17/README.md).
- Earlier 115200 pre-modification captures opened COM3, waited 60 seconds and
  reported zero bytes on tested contacts. They do not establish successful
  nonempty raw capture; rx.bin/session.json from those runs were not supplied.
- The corrected default path/38400 version is in source; a separate Windows
  execution result for that exact script revision was not supplied.
- Later v0.1.1 help established switch input and output in the described pin-2
  RX connection. [New evidence](evidence/2026-10-17-switchlens/README.md).
  Recovery remains untested.

Byte-reading API: [Microsoft SerialPort.Read](https://learn.microsoft.com/en-us/dotnet/api/system.io.ports.serialport.read).
Logs are local/ignored by Git. Selected supplied files were published separately
at the owner's explicit request, not automatically by this script.
