**English** | [Русский](TP-LINK-REPORT.ru.md)

# Vendor report: unauthenticated TDDP factory-MAC modification

Updated 18 October 2026 with owner-run hardware evidence. The owner reports having
submitted an earlier report; this is an evidence update for that report. The
assistant has not sent this update to TP-Link.

## Product and scope

- TP-Link TL-SG1218MPE(UN) V5, stock base 1.0.0 Build 20230616.
- Hardware test: owner-reported SwitchLens **v0.1.4**, a modified image.
- Stock update SHA-256:
  `c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
- v0.1.4 SHA-256:
  `4093f2e0dfcbbbc1c0caf0ed1d9d8902de747aa41e9525840b4755004e791b93`.

The reviewed TDDP, factory-write and flash-driver ranges in the archived v0.1.4
and official image are byte-identical: [Log 008](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6250781077).
This supports attribution to inherited stock code; a fresh live reproduction on
an unmodified official installation is still requested from the vendor.

## Confirmed hardware result

At **2026-10-18 14:05:00 UTC**, an owner-run PowerShell probe supplied no credentials
and performed the following on one switch:

| Operation | Observed result |
|---|---|
| Read factory MAC | Original MAC returned |
| Write a distinct locally administered MAC | Matching ACK |
| Separate factory-MAC read | New MAC returned |
| Write original MAC back | Matching ACK |
| Separate factory-MAC read | Original MAC returned |

Result: `CHANGED_FACTORY_READBACK_WITHOUT_CREDENTIALS_CONFIRMED`.
Restoration: `ORIGINAL_MAC_READBACK_CONFIRMED`. No errors.

[Full owner output and exact script — Log 010](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6250854017).
The changed independent readback, not the ACK alone, demonstrates unauthorized
factory-MAC modification on the tested device.

An earlier owner run at **2026-10-18 07:55:18 UTC** received no reply to the
initial MAC read, received a response to the credential-free control exchange,
then read the expected MAC. The later write test began with reading already
available; it did not repeat the control exchange or begin from a fresh reboot.

## Code path and write extent

TDDP listens on UDP **1040** and replies to UDP **61000**. Callback
`0xbfc4e238` handles opcode 12 by transitioning state 2 to 0 after successful
response transmission, without a credential check in the reviewed path.
Opcode 6 copies six bytes into factory setter `0xbfc52ff0`, which invokes
helper `0xbfc52edc`. Opcode 15 reads through `0xbfc54018` from the
memory-mapped factory-flash region, with a default-value fallback for all-FF MAC.

The helper preserves 194 bytes, requests erasure of sector 508 (nominal
4 KiB at offset `0x1fc000`), then rewrites 194 bytes. The owner's verified
historical dump has only FF in the remaining 3,902 bytes. That does not establish
the current full-sector contents. Software program protection does not by
itself prevent the preceding erase attempt; hardware protection was not captured.
See [journal, Logs 002–007](https://github.com/adsdevdoo/switchlens-sg1218/issues/1).

## Reproduction artifacts

- [Pinned write/readback script](https://github.com/adsdevdoo/switchlens-sg1218/blob/08c4c57b28031bedaedae68c65eab6d0916922ed/tools/Confirm-TddpMacWrite.ps1).
  Default mode checks the reviewed backup and expected MAC **offline**.
  Explicit `-Execute` sends the write/readback sequence and attempts restoration.
  The backup hash guard intentionally binds this version to the owner's unit;
  vendor engineers should reproduce on their own backed-up lab device.
- [Read-only handshake probe](../tools/Confirm-TddpHandshake.ps1).
- [Offline MIPS audit](../tools/audit_management_auth.py) and
  [recorded results](management-auth-results.json). Run
  `python tools/audit_management_auth.py` after installing
  `requirements-dev.txt`. These earlier tests stubbed persistence/network
  helpers and do not independently demonstrate physical writes.

The live write script erases/reprograms the factory sector. Restoration is
best effort. It sends no reboot/reset and saves evidence after each step.

## Limits and impact

Confirmed impact is unauthenticated modification of a factory identifier by a
client able to reach the service on the tested network. Only the six MAC bytes
were read back after restoration; full-sector integrity was not independently
reread. Power-cycle persistence, Internet reachability, other firmware versions,
arbitrary code execution and other factory writes were not demonstrated.
No intentional backdoor is alleged. The reviewed TSDP type-3 path checks the
configured username/password; this is not a claim of a universal TSDP bypass.

## Requested vendor action and mitigation

Please reproduce on official V5 firmware, investigate affected versions and
network scope, and disable unnecessary production factory services or enforce
authentication and authorization before every factory operation.

SwitchLens v0.1.5 contains a defensive patch disabling TDDP/TSDP entry points.
It is a custom mitigation, not a vendor fix; installation and validation of the
mitigation on the owner's hardware have not yet been confirmed. Management-network
access restrictions are a containment measure, not proof of a firmware fix.
