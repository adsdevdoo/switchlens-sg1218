**English** | [Русский](AUDIT-PROGRESS.ru.md)

# Audit checkpoint — 18 October 2026, updated after patch-3

This is the current continuation checkpoint for the owner-authorized review of TL-SG1218MPE(UN) V5, reported running SwitchLens v0.1.4 on stock base 20230616. It supersedes the earlier read-only-stage checkpoint.

## Confirmed on the owner's switch

- Target: 192.168.1.3; original MAC 58:04:4F:95:41:A1.
- At 07:55 UTC, an unauthenticated TDDP control exchange enabled a subsequent MAC read.
- At 14:05 UTC, the owner ran the controlled factory MAC write/readback probe: original MAC → temporary 5A:04:4F:95:41:A1 → readback of the changed value → restore original → readback of the original. No credentials, reboot or power cycle; errors list empty.
- Result: **CHANGED_FACTORY_READBACK_WITHOUT_CREDENTIALS_CONFIRMED**. The earlier statement that no changed readback had been observed is obsolete.
- Reading the modified value is confirmed. Persistence across reboot/power loss, arbitrary flash access, remote code execution, deliberate vendor backdoor and ongoing exploitation are **not** established.
- Additional unauthenticated reads returned the 40-byte factory field and eight-byte flash UID. These reads are separate from proof of write access to those fields.

The owner reports previously contacting TP-Link. The assistant has not sent vendor mail.

## Evidence anchors

- [Issue #1](https://github.com/adsdevdoo/switchlens-sg1218/issues/1): detailed journals, owner outputs and scripts.
- [Write result and script journal](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6250854017).
- [Vendor report](TP-LINK-REPORT.md).
- [Original flash backup](../backups/original/2026-10-17/GD25Q16B-xgpro-original.bin): 2,097,424 bytes, SHA-256 b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87.
- Stock web-upgrade BIN: 1,013,324 bytes, SHA-256 c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32.

## Device-side code already traced

The TDDP path reaches the real erase/program helper at VA 0xbfc52edc (file offset 0x4aedc). It copies 0xC2 bytes from factory flash 0xb41fc000, patches a selected field in RAM, erases sector 0x1FC and programs those 0xC2 bytes. Wrappers select MAC offset 0/length 6, signature offset 6/length 128, and field40 offset 0x96/length 40.

The real flash driver writes SPI controller registers. There is no additional password check in the reviewed helper bodies. Wrappers return zero after the call, so acknowledgement alone would not prove success; the owner's changed readback supplies the stronger evidence.

The MAC getter at 0xbfc54018 reads memory-mapped factory flash, with a special fallback for one constant. The owner also verified that the inspected archived sector tail was all FF. That archival check is not a current full-sector hardware dump.

## Field40 remains unidentified

- Flash offset 0x1FC096; 40 ASCII characters.
- Live value matches the archived backup.
- It does not equal SHA1 of the stored raw 128-byte signature.
- It does not equal SHA1 of the raw eight-byte flash UID.
- Its length alone does not establish a password, secret key, activation token or hash algorithm.
- The utility's one-byte isFactory discovery property has not been linked to field40 or to enabling TDDP writes.

Do not repeat previously disproved hash guesses as findings.

## Easy Smart utility analysis completed so far

[English/Russian report and artifacts](easysmart/README.md).

The owner supplied 100 selected Java classes from the installed utility and then request metadata for six omitted classes in patch-3. The 100 raw class lengths/hashes were recomputed and checked; the later metadata's lengths and offsets were checked, while its per-class hashes remain extractor-reported.

Confirmed client facts:
- 32-byte management header; usual UDP destination/local ports 29808/29809, with a client fallback pair 62576/62577.
- DISCOVERY/GET/SET wire opcodes 0/1/3.
- SET requests receive username/password TLVs 0x0200/0x0202 from the shared sender.
- Login is followed by GET TLV 0x000A for the number of switch ports.
- The recovered 256-byte legacy encryption key exactly matches stock BIN [0xCB2E8,0xCB3E8). This establishes a shared recoverable transport key, not a new login bypass.
- Simulator credentials and demo strings in the utility are not evidence of hidden device accounts.
- A complete utility audit and all TLV mappings are not finished. The reduced discovery metadata omits branch destinations; do not guess remaining tag assignments.

[Journal 021](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6251784938) and [journal 022](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6251922477) contain reproducible scripts and results. Automatic approval review rejected publication of a separate full bytecode listing; the source export, analysis scripts and summaries were preserved.

## Mitigation and next concrete step

[SwitchLens v0.1.5](../releases/v0.1.5/README.md) disables initialization and receive handlers for TDDP/TSDP. Easy Smart discovery/configuration therefore stops; administration uses the known-IP web interface.

Current artifact was fetched and checked directly:
- SHA-256 b2617a639869cf5ca0ef7b953b321f0625f3a1af3c6aab8d1a37a7ffa3dd6a7d.
- CRC32 ff2c1e25, matching the manifest.
- Four service patches at file offsets 0x3fcf0, 0x45668, 0x40db0, 0x46238 match the early-return instructions.
- Earlier recorded 26 MIPS checks passed; they were not rerun for this checkpoint.
- **Hardware boot/installation of this exact BIN remains unconfirmed.**

Next: install through the existing web upgrade page on the matching owner's device; capture v0.1.5 build and disabled-service boot markers; verify web login, authenticated stats, UART/cooling and ordinary switching/PoE. Then repeat the prior handshake/MAC-read probe, with no write test. UDP silence alone remains inconclusive: correlate with build/boot evidence and working network connectivity.

[Mitigation journal](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6252045870).

## Continuation workflow

Record each completed check immediately in issue #1 and read back the comment. Include action, source/script, result, limits and next step. Label hypotheses. All owner-side Windows output goes under C:\tmp. Current shell environment is disconnected; GitHub and pure JavaScript data processing work. Do not claim local, emulator or hardware execution unless actually performed.
