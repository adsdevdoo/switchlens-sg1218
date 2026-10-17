**English** | [Русский](SECURITY-AUDIT.ru.md)

# Stock management security review — 17 October 2026

The review found a fixed-key RC4 credential/message codec and TDDP factory-write
paths that do not consult the web session in selected internal states.
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
| TDDP management | Initializer `0xbfc4d668`, called through `0xbfc4d6f8`, registers callback `0xbfc4e238` and binds UDP 1040. In forced states 0/1, three selected callback branches reach the factory-write helper with HTTP session inactive and without calling the credential getter. States 2/3 reject these same requests. **Initialized state is 2**, so callback tests alone do not prove live reachability. |
| Factory persistence | Helper `0xbfc52edc` copies factory data from `0xb41fc000`, changes selected bytes, calls sector erase and writes back `0xc2` bytes. Emulator tests stop at this helper and record calls; they never execute physical flash writes. |
| HTTP authentication | Login handler `0xbfc3f8e0` compares configured credentials, with a second representation-conversion path. No independent master password was identified in this reviewed path. That does not exclude hidden accounts elsewhere. HTTP transport itself remains unencrypted. |

The existing [Easy Smart research](https://geekly.dev/easy-smart-report-main/)
describes fixed-key RC4 weaknesses in other revisions, including SG1218MPE V1–V4.
It does not list V5. The V5 findings above come from this exact binary; other
products' CVEs must not be assumed to apply automatically.

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
