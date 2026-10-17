**English** | [Русский](ROADMAP.ru.md)

# SwitchLens roadmap

Status after the first successful v0.1.1 hardware test, **17 October 2026**.
[Evidence](evidence/2026-10-17-switchlens/README.md) · [JSON reference](JSON-API.md) · [Handoff](CONTEXT.md).

| Stage | Status / remaining criterion |
| --- | --- |
| Runtime analysis | Required paths identified; additional MIB meanings remain provisional |
| JSON contract and host prototype | Locally tested; all fields documented |
| Boot, signature, RAM/flash | CRC/staging traced and boot observed; peak stack/IRQ behavior and recovery outstanding |
| Timer / uptime | Raw counter changes on hardware; time unit unconfirmed |
| Stock bench | SPI export saved; UART at 38400 8N1, R41/R42 populated with 0 Ω 0402 |
| v0.1.1 package | Published in GitHub Releases; 20 MIPS tests plus host checks |
| Web installation and boot | Confirmed on owner's unit |
| UART CLI | RTK# and help confirmed; other commands not exercised |
| `/stats.json` | Two complete schema-valid replies, 18 ports, changing counters |
| Accuracy and UI agreement | Compare all settings/ports and counters against known traffic |
| PoE under load | Only OFF/0 W observed; real PDs and measurement comparison pending |
| Extended testing | Sustained traffic, memory/CPU, multiple HTTP clients and real PDs pending |
| Recovery / rollback | Untested; owner declined repeat desoldering as a preliminary prerequisite |
| Prometheus / Grafana | Next integration goal; exporter/dashboard not yet created |
| Production deployment | Separate owner decision after bench checks |

Next: connect a real PoE consumer and compare JSON with the stock page, then
verify physical numbering/settings, discard causes and uptime scale. Two manual
requests do not establish a safe continuous polling interval.

This is working firmware; the successful first run does not close recovery or
stress testing. The owner proceeded with web installation without another
preliminary desoldering test. Do not turn the old planning checklist into a new
mandatory condition for continuing.

[Vendor ZIP/BIN archive](../vendor/tp-link/tl-sg1218mpe-v5/README.md),
[datasheets](datasheets/README.md), [implementation and emulator scope](FIRMWARE.md).
Unknown fields remain null. Provisional MIB names are not promised IF-MIB equivalents.
