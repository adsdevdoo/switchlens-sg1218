**English** | [Русский](SECURITY-AUDIT.ru.md)

# Stock management security review — 17 October 2026

The review found a fixed-key RC4 credential/message codec and a TDDP path from
initialized state 2 to factory-write calls without credential verification.
This transition is reproduced in an offline MIPS emulator for stock and v0.1.4.
**An intentional vendor backdoor is not established. Live unauthenticated
factory writes have not been demonstrated.** SwitchLens v0.1.5 disables both
TDDP and TSDP initialization and receive entry points as a defensive measure.

Scope: TL-SG1218MPE(UN) V5, stock 20230616 update SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
Methods: disassembly, references, original MIPS routines executed with synthetic
inputs in Unicorn. No packets were sent to the device and no real credentials
were decoded. Flash-writing and socket functions were mocked.

## Findings

| Finding | Evidence and practical limit |
|---|---|
| Fixed RC4 key | 256 bytes at file `0xcb2e8`, VA `0xbfcd32e8`; SHA-256 `003d481f74298dfb9cd27e69c74405a1bb949af5c5591dedea18c284ea828b54`. The key is embedded in the firmware, not unique to the owner's password. |
| Reversible credentials | Routine `0xbfc47c38` transforms 16 bytes of each username/password buffer using the same key and fresh RC4 state. Synthetic MIPS output matches an independent RC4 implementation; applying it twice restores input. Getter `0xbfc543a4` reads configured credentials from RAM/flash and invokes this routine. This is not password hashing. |
| TSDP management | Initialization `0xbfc47cf0` registers callback `0xbfc48db0` and binds UDP 29808. The receive routine calls RC4 before later header/session checks. The fixed key provides no device-specific secrecy. We have not established that every TSDP operation bypasses authentication. |
| TDDP management | Initializer `0xbfc4d668`, called through `0xbfc4d6f8`, registers callback `0xbfc4e238` and binds UDP 1040. The follow-up below reproduces a transition from initialized state 2 to state 0, then three factory-write calls, without credentials. Successful reply transmission is mocked. Live network reachability remains unverified. |
| Factory persistence | Helper `0xbfc52edc` copies factory data from `0xb41fc000`, changes selected bytes, calls sector erase and writes back `0xc2` bytes. Emulator tests stop at this helper and record calls; they never execute physical flash writes. |
| HTTP authentication | Login handler `0xbfc3f8e0` compares configured credentials, with a second representation-conversion path. No independent master password was identified in this reviewed path. That does not exclude hidden accounts elsewhere. HTTP transport itself remains unencrypted. |

The existing [Easy Smart research](https://geekly.dev/easy-smart-report-main/)
describes fixed-key RC4 weaknesses in other revisions, including SG1218MPE V1–V4.
It does not list V5. The V5 findings above come from this exact binary; other
products' CVEs must not be assumed to apply automatically.

## Follow-up: initialized-state transition and TSDP authentication

The earlier archived v0.1.5 audit forced TDDP states 0/1; it did not prove how
those states are reached. The new [offline audit](../tools/audit_management_auth.py)
and [results](management-auth-results.json) close that specific code-analysis gap.
They pin the SHA-256 of stock, v0.1.4 and v0.1.5; the release BINs are unchanged.

**TDDP:** state at `0xbf0015c0` starts at 2. The startup loop at
`0xbfc08684..0xbfc086a4` clears BSS, including counter `0xbf013690`;
executing that loop separately confirms zero, while preserving state 2.
In callback `0xbfc4e238`, the branch at `0xbfc4e314..0xbfc4e384` accepts
a control request with opcode 12/type 1. When the counter is nonnegative and
the reply-send function returns success, the handler stores state 0. This
branch does not check a password or an HTTP session.

Starting with the image's state 2 (not forcing state 0), the emulator then
reaches factory helper `0xbfc52edc` for each selected command:

| Opcode | Offset within factory data | Length |
|---|---|---|
| 6 | `0x00` | 6 bytes |
| 14 | `0x96` | 40 bytes |
| 11 | `0x06` | 128 bytes |

The same commands sent before the transition are ignored. Wrong control type
and failed reply transmission leave state 2. No credential getter is invoked.
The helper is intercepted before persistence: there is no flash erase/write.
Both stock and v0.1.4 behave this way; v0.1.5 returns immediately with zero
helper calls and no responses. This supports **missing authentication in the
reviewed TDDP factory-management path**, not an allegation of deliberate intent.

**TSDP:** fixed-key encryption does not mean every command bypasses login.
The type-3 path checks a 16-bit session token, parses username/password TLVs,
and calls credential comparison at `0xbfc47e74` before command dispatch.
The new tests execute decryption and parsing from the original callback entry,
with a synthetic configured account and MAC. Missing credentials are rejected
(error 3); a wrong password is rejected (error 7); matching credentials reach
`0xbfc49124`, immediately after successful authentication. A wrong token returns
before credential lookup. An unauthenticated type-1 request for password TLV
`0x0202` is rejected (error 2). These are selected valid-format cases, **not**
an exhaustive malformed-packet or authorization-bypass audit. Type 0/1 have
separate pre-authentication discovery/read handling; their existence alone
does not establish arbitrary unauthenticated configuration access.

There are 33 bounded checks across the three images: 3 startup-loop checks,
9 TDDP sequences, 6 negative TDDP controls and 15 TSDP cases. All pass.
TSDP execution deliberately stops at rejection/authentication checkpoints;
socket creation, bind and credential storage reads are synthetic dependencies.
No complete boot, packet transport or physical persistence is emulated.

The owner's v0.1.4 probe reported no matching reply to a single MAC-read
request without this control exchange. That result neither proves nor disproves
the path above: state 2 ignores the direct request in the emulator. The actual
device state and packet delivery during that probe were not observed.

Reproduce locally with the repository's Python development dependencies:

```sh
python tools/audit_management_auth.py
```

## v0.1.5 mitigation

| File offset | Entry point | Change |
|---|---|---|
| `0x3fcf0` | TSDP initializer | Return immediately; no socket registration/bind |
| `0x45668` | TDDP initializer | Return immediately; no socket registration/bind |
| `0x40db0` | TSDP receive callback | Return before accessing input |
| `0x46238` | TDDP receive callback | Return before accessing input |

Each entry is replaced with `jr ra; move v0, zero` (delay slot included).
The builder verifies exact original bytes and restricts changes to an allowlist.
Boot service messages are updated. The HTTP initializer and both stock HTTP
authentication gates remain unchanged. The stock credential codec remains to
preserve login and configuration compatibility: changing its key without
migrating stored credentials would break existing logins.

The firmware no longer supports TP-Link utility discovery/configuration through
these services. Normal web management, authenticated JSON and UART are retained.
Only the two application services are disabled; DHCP/IGMP ASIC trap setup stays
unchanged. This does not mean all UDP traffic is disabled.

## Reproducible evidence

- [Audit script](../tools/audit_security.py): synthetic RC4 round trip, 12 TDDP
  callback/state cases and a literal HTTP route inventory.
- [Machine-readable findings](../releases/v0.1.5/security-audit.json).
- [Mitigation checks](../tests/test_security.py) and [results](../releases/v0.1.5/security-test-results.json): stock initializers bind expected ports; patched initializers do not create sockets; patched receive entries return even with unmapped input; boot service segment continues and retains conditional HTTP startup; authentication/credential blocks and the configuration tail remain unchanged.
- [v0.1.5 image, hashes and all 26 MIPS checks](../releases/v0.1.5/README.md).

The exact v0.1.5 image still needs hardware installation and network verification.
The checks are bounded CPU tests, not a whole-device boot or a proof of absence
of vulnerabilities. No exhaustive indirect-call, hidden-account, remote-code-
execution or complete packet-parser audit has been performed. Literal routes
such as `/httpupg.cgi`, `/reset.cgi` and `/conf_restore.cgi` are normal management
surface candidates, not evidence of secret access merely because their names
appear in the image.

Remaining work: protect the HTTP management network; separately design migration
away from reversible credentials if required; inspect remaining management
handlers. Fixed-key credential storage and plaintext HTTP are **not fixed** by
the service-disable patch. Do not publish real cookies/passwords when validating.
