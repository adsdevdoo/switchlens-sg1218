**English** | [Русский](README.ru.md)

# Stock UART evidence — 17 October 2026

This is the historical stock-firmware session. Later that day the working
SwitchLens v0.1.1 completed web upgrade, UART help and dynamic JSON:
[successful test journal](../2026-10-17-switchlens/README.md).

The owner explicitly requested these complete supplied logs/screenshots be
published. The boot text includes this unit's MAC; authorization is limited to
these materials, not automatic future publication.

- Owner confirmed series-gap continuity, R41/R42 populated with **0 Ω 0402**,
  and J2 pin 1 as TX.
- The message “38400 отлично работает” (“38400 works perfectly”) and readable
  output establish **38400, 8N1, no flow control**.
- [boot-stock-38400.txt](boot-stock-38400.txt) is the full pasted text from check
  runtime img to code init. Lines/MAC are retained, UTF-8/LF; it is not raw UART
  data. Original rx.bin/session.json were not supplied.
- Screenshots are unchanged; original names/hashes are in
  [sources.json](../../images/sources.json). [Main guide](../../../README.md).
- Zero-data attempts are available only as screenshots. The second zero capture
  belongs to pin 1 according to the owner's correction, not pin 2. No binary
  logs were reconstructed from images.
- At this historical stage RX commands, bootloader menus, recovery and modified
  firmware were untested. The later successful session resolves initial runtime
  boot and help; recovery remains unverified. This stock SignCheck Pass alone
  does not establish acceptance of a modified image.

J2 numbering follows the owner's measurement convention. Photograph orientation
and a factory marker were not independently tied to it; do not transfer the
numbering to another board without checking.
