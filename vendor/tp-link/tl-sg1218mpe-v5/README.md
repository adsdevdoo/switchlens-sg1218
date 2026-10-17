**English** | [Русский](README.ru.md)

# Official TP-Link TL-SG1218MPE(UN) V5 firmware

Four archives were downloaded on 17 October 2026 from links on the
[TP-Link V5 support page](https://www.tp-link.com/us/support/download/tl-sg1218mpe/v5/).
Original ZIP bytes are retained. BIN/PDF contents were extracted unchanged,
with simplified local names. [sources.json](sources.json) records original
archive names, URLs, sizes and hashes.

| Build | Original archive | Update image | TP-Link publication date | Vendor change summary |
| --- | --- | --- | --- | --- |
| 20220921 | [ZIP](20220921/TL-SG1218MPE-UN-V5-1.0.0-Build-20220921.zip) | [BIN](20220921/TL-SG1218MPE-UN-V5-1.0.0-Build-20220921-up.bin) | 2022-10-08 | First V5.0/V5.6 release |
| 20221012 | [ZIP](20221012/TL-SG1218MPE-UN-V5-1.0.0-Build-20221012.zip) | [BIN](20221012/TL-SG1218MPE-UN-V5-1.0.0-Build-20221012-up.bin) | 2022-10-26 | Loop-detection fix; V5 |
| 20230220 | [ZIP](20230220/TL-SG1218MPE-UN-V5-1.0.0-Build-20230220.zip) | [BIN](20230220/TL-SG1218MPE-UN-V5-1.0.0-Build-20230220-up.bin) | 2023-02-20 | Management-protocol security change; V5/V5.6 |
| 20230616 | [ZIP](20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616.zip) | [BIN](20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin) | 2023-07-24 | First-power-on PoE and security fixes |

Each folder also contains its `TP-Link-Upgrade-Guide.pdf`. Hardware compatibility
in this table is vendor information, not a SwitchLens test on V5.6.

| Material | Purpose |
| --- | --- |
| Official ZIPs | Unchanged manufacturer distributions |
| Official `*-up.bin` | Update images, each 1,013,324 bytes; not full 2 MiB SPI dumps |
| [Original unit export](../../../backups/original/2026-10-17/README.md) | 2,097,424 bytes including a 272-byte export trailer |
| [SwitchLens 0.1.1](../../../releases/v0.1.1-experimental-uart/README.md) | Working modified firmware: boot, UART and JSON confirmed on owner's unit; recovery untested |

The extracted 20230616 matches the builder's expected input:

```text
c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32
```

Older builds are archived for research, not proof of permitted/tested downgrade.
Recovery remains a separate [bench](../../../docs/LAB.md) concern.

From this directory:

```bash
sha256sum -c SHA256SUMS
```

```powershell
Get-ChildItem -Recurse -File | Where-Object Extension -In '.bin','.zip','.pdf' |
    Get-FileHash -Algorithm SHA256
```

Compare with SHA256SUMS/sources.json. These hashes are our file checks, not vendor
signatures. Files were included at the owner's request. Firmware/manual rights
remain with TP-Link and other rights holders; project source licensing does not
cover them. Original license notices remain inside ZIP/PDF files.
