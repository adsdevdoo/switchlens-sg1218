**English** | [Русский](TP-LINK-REPORT.ru.md)

# Draft for vendor review: TDDP factory-management authentication

Status: prepared for owner review; not submitted. Live verification pending.

## Product and affected image

TP-Link TL-SG1218MPE(UN) V5, firmware 1.0.0 Build 20230616.
Official update SHA-256:
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
The issue also reproduces in the derived SwitchLens v0.1.4 image.

## Finding and impact

The TDDP receive callback at `0xbfc4e238` has a control exchange that moves its
initialized state from 2 to 0 without credential verification, conditional on
successful response transmission. Subsequent selected requests reach factory
data persistence at `0xbfc52edc` without credential verification. This may allow
unauthorized modification of factory data if this UDP service is reachable.
We have not demonstrated physical flash writes, arbitrary code execution, or
an intentional backdoor. This report does not allege a universal TSDP bypass:
the reviewed TSDP type-3 path checks the configured username and password.

## Reproduce without touching hardware

From the repository root, install `requirements-dev.txt` and run:

```sh
python tools/audit_management_auth.py
```

This executes the original MIPS bytes in Unicorn. It checks the boot BSS-clear
loop, starts TDDP with its initialized state 2, executes the control exchange,
and records three calls to the factory persistence helper. The helper and
network transmission are stubbed; no packets or flash writes occur. Expected:
stock/v0.1.4 transition to 0 and reach the helper; v0.1.5 does neither.
See [full evidence](SECURITY-AUDIT.md) and [recorded results](management-auth-results.json).

## Optional live corroboration: handshake and MAC read only

Download [Confirm-TddpHandshake.ps1](../tools/Confirm-TddpHandshake.ps1).
Close Easy Smart Utility so local UDP port 61000 is available. In PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Confirm-TddpHandshake.ps1 -SwitchIP <YOUR_SWITCH_IPV4>
```

The script sends at most three unicast requests to UDP 1040: initial MAC read,
control exchange if needed, then another MAC read. It supplies no credentials,
performs no configuration/flash write, reset, reboot or firewall changes.
It can change transient TDDP state in RAM. The JSON includes request/reply bytes,
transaction IDs, sender port and MAC. Matching replies must originate from the
requested IP and match the expected header, size and transaction.

`HANDSHAKE_AND_MAC_READ_WITHOUT_CREDENTIALS_CONFIRMED` corroborates the network
entry and read path, **not physical flash-write access**. An already-available
MAC read is reported separately. Silence/errors are inconclusive. Windows
PowerShell execution remains to be confirmed by the owner; the exact request
sequence and expected replies were checked against all three images in MIPS.
No successful live result is asserted here. Redact the owner's IP/MAC before
publicly sharing results; keep originals for private vendor review if desired.

## Requested vendor action

Please verify reachability in the official V5 firmware and whether the factory
operations are intended to be remotely accessible without authentication.
Disable the production service or enforce authentication/authorization before
all factory writes. SwitchLens v0.1.5 defensively disables TDDP/TSDP entry
points; that custom patch is not a vendor fix and is not yet hardware-verified.
