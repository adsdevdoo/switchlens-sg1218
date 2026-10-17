**English** | [Русский](README.ru.md)

# SwitchLens chip datasheets

Downloaded 17 October 2026 from public mirrors. [sources.json](sources.json)
records URLs, versions, dates, sizes and hashes. PDFs are unchanged; original
CONFIDENTIAL/copyright notices remain. Project licensing does not cover them.

| Document | Applicability to this board | Subject |
| --- | --- | --- |
| [GD25Q16B rev. 2.3, 49 pages](GD25Q16B_Datasheet_2.3.pdf) | U6 GD25Q16BSIG visible in [photo](../images/uart/flash-marking.jpeg); PDF revision from final history entry on p.49 | SPI NOR pinout, power, commands, protection/security and package |
| [RTL8214FC rev. 1.2, 63 pages](RTL8214FC-VC-CG_Datasheet_1.2.pdf) | RTL8214FC visible in [photo](../images/rtl8214fc-marking.png); full VC-CG suffix unconfirmed | PHY pins, power, interfaces and registers |
| [RTL8380M/RTL8382M/RTL8382L rev. 1.0, 101 pages](RTL8380M_RTL8382M_RTL8382L_Datasheet_1.0.pdf) | Family hypothesis; exact chip under heatsink not identified | UART, SPI, boot modes and switching |
| [RTL8382L rev. 1.2, 45 pages](RTL8382L_Datasheet_1.2.pdf) | Candidate documentation, not proof that this chip is installed | Additional candidate information |

RTL838x evidence includes the stock-BIN string
`realtek_mcu/CPU_RTL838x_RTL833x/EasySmart_V3/.../dal/maple/dal_maple_l2.c`
at `0xd3094`; see [initial analysis](../../research/REPORT.md). Family similarity
does not establish exact chip/pin compatibility.

## PDF navigation

Page counts include the cover as page 1, not printed page numbers.

- GD25Q16B: features p.4, pinout p.5, organization p.7, status registers pp.11–12,
  commands pp.13–34, security pp.32–34, supply pp.35–37, ordering code p.41,
  SOP8 208mil p.43.
- RTL8214FC: Register Description starts p.36.
- Combined RTL838x: SPI pp.29/43/56 and UART pp.30/44/56 for 8380M/8382M/8382L.
  MIB section p.77 does not independently establish all register semantics here.
- RTL8382L rev.1.2: SPI p.19.

A SoC pinout is not the J2 header pinout. Do not derive J2 connections without
identifying the chip and verifying board traces.

## U6: GD25Q16BSIG

Datasheet pp.4/5/41 specify 16 Mbit (2 MiB) SPI NOR, 2.7–3.6 V.
S = SOP8 208mil, I = −40…+85 °C, G = lead/halogen-free. These are chip
specifications, not UART voltage measurements.

Top-view chip pinout from p.5; **these are U6 pins, not J2**:

| U6 pin | Signal |
| --- | --- |
| 1 | CS# |
| 2 | SO / IO1 |
| 3 | WP# / IO2 |
| 4 | VSS / GND |
| 5 | SI / IO0 |
| 6 | SCLK |
| 7 | HOLD# / IO3 |
| 8 | VCC |

Security registers exist outside the main array (pp.4,32–34); their presence in
the supplied export is unconfirmed. [Original export and 272-byte trailer](../../backups/original/2026-10-17/README.md).

## Other observations

PoE-controller, other PHY and power-chip readable markings were not supplied;
matching datasheets are not identified. The owner uses XGecu T56. CP2102/COM3
loopback succeeded; selecting 3.3 V is not an independent TXD measurement.
Owner-established board facts: R41/R42 0 Ω 0402, J2 pin 1 TX, 38400 8N1/Flow None.
Later v0.1.1 help confirms two-way exchange in the described wiring; see [bench](../LAB.md).
These board observations were not inferred from candidate SoC pinouts.

Verify originals from this directory:

```bash
sha256sum -c SHA256SUMS
```

PowerShell: `Get-FileHash *.pdf -Algorithm SHA256`, compare with SHA256SUMS.
