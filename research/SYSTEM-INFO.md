**English** | [Русский](SYSTEM-INFO.ru.md)

# System Info field sources

Original analysis16 October2026; [source record](SYSTEM-INFO.txt). The first
screenshot was checked against JS at file99cce and handler37388:376f8.
Original personal addresses were not inserted into synthetic examples. Later
real JSON was published separately at the owner's request.

| UI field | JSON field | Stock info_ds |
| --- | --- | --- |
| Device Description | system.description | descriStr |
| MAC Address | system.mac | macStr |
| IP Address | system.ip_address | ipStr |
| Subnet Mask | system.subnet_mask | netmaskStr |
| Default Gateway | system.default_gateway | gatewayStr |
| Firmware Version | system.firmware_version | firmwareStr |
| Hardware Version | system.hardware_version | hardwareStr |

All seven fields are implemented. Preserve full hardware/firmware strings, not
only revision digits. `name` is a compatibility alias of description. `model`
is separate from editable description; the current exact-image adapter uses
the constant TL-SG1218MPE rather than inferring it from user text.

| Source | Static evidence |
| --- | --- |
| Description | Page374a8 → BFC51370 → BFC51E18, copies33 bytes from BF0015FC or B41FE008 using BF0015F0, NUL at offset32; expose max32 bytes and JSON-escape |
| MAC | Page37490 → BFC51378 → BFC280B0 unit0; formatter BFC314B8; current adapter reads actual ASIC MAC registers |
| IPv4/mask/gateway | Page374b8 → BFC50FBC; file48fbc:4902c copies4 bytes from BF016D3A/3E/42; formatter BFC3147C; preserve byte order |
| Firmware | Page374e4 → BFC51030,64 bytes from BF014348; bounded read, no assumed NUL beyond buffer |
| Hardware | Page374ec → BFC512C0; string BFCE02F4/filed82f4 |

HTML contains demo TL-SG105E/MAC/old-version placeholders, replaced by loadValue
from info_ds. Never use those literals as live identity. The stock image did
not have stats.json at the time of analysis; the working modified firmware now
does. [Current API](../docs/JSON-API.md), [hardware samples](../docs/evidence/2026-10-17-switchlens/README.md).
