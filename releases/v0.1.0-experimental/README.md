**English** | [Русский](README.ru.md)

# SwitchLens v0.1.0 — archived JSON-only package

The original tagged package for TL-SG1218MPE(UN) V5.0 is retained unchanged.
**Current working firmware is [v0.1.1](../v0.1.1-experimental-uart/README.md)**,
which uses this JSON payload and adds UART CLI. v0.1.0 itself was not independently
installed/tested on hardware. The historical filename/tag is not renamed.

- [BIN](SwitchLens-SG1218MPE-V5-v0.1.0-experimental.bin)
- [SHA256SUMS](SHA256SUMS), [release manifest](release.json), [build manifest](build-manifest.json)

The dynamic GET endpoint uses stock session authentication and provides system,
18-port counters/status, PoE and Auto Recovery. Unsupported values are null;
some additional MIB semantics remain provisional. Base: official
`1.0.0 Build 20230616 Rel.57668`; internal strings are unchanged.

Verified offline: size **1,013,324 bytes**, SHA-256
`58d48cf69cac4024eddfb4ede1bb5a925420521a0f0e44011ff4fa08940c2e25`,
CRC32 `5e9ceeca` over `[0x10,0xf7000)`, field at 0; source/build hashes match
manifest. [MIPS results](../../docs/target-test-results.json),
[implementation](../../docs/FIRMWARE.md).

Later bench evidence applies to v0.1.1: web boot, RTK#/help, two changing JSON
replies on the Ver:5.40 board. [Hardware record](../../docs/evidence/2026-10-17-switchlens/README.md).
Loaded PoE, sustained operation and recovery remain outstanding. The original
SPI export and stock UART are archived; do not infer a recovery menu from runtime CLI.
The owner's decision against preliminary repeat desoldering is recorded in [LAB](../../docs/LAB.md).

```powershell
Get-FileHash .\SwitchLens-SG1218MPE-V5-v0.1.0-experimental.bin -Algorithm SHA256
```

```bash
sha256sum -c SHA256SUMS
```
