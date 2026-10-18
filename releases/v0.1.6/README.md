**English** | [Русский](README.ru.md)

# SwitchLens v0.1.6 — session-independent statistics

[**Download web-upgrade BIN**](https://github.com/adsdevdoo/switchlens-sg1218/releases/download/v0.1.6/SwitchLens-SG1218MPE-V5-v0.1.6.bin)
· [Repository BIN](SwitchLens-SG1218MPE-V5-v0.1.6.bin)
· [SHA256SUMS](SHA256SUMS) · [Build manifest](build-manifest.json)

For **TP-Link TL-SG1218MPE(UN) V5.0**, stock base `1.0.0 Build 20230616 Rel.57668`.
This is v0.1.5's hardened feature set plus exact anonymous `GET /stats.json`.
**Pre-release: hardware installation and real simultaneous browser/collector
operation are not yet verified.** Last owner-confirmed installed build: v0.1.4;
v0.1.5 was prepared but its hardware test was deferred.

## Changes

- No login, password, cookie, token or preliminary request for exact `GET /stats.json`.
- The raw request is recognized before the outer IP/session gate and timeout refresh.
  Statistics neither create nor replace a session, change its cookie/IP, nor extend it.
- Web panel, settings, firmware update and reboot retain stock authentication.
  Query strings, similar paths and other HTTP methods receive no exception.
- Schema version 1, metric fields/values, content type and no-store behavior retained.
  `X-SwitchLens-Build: v0.1.6`; vendor firmware version string remains unchanged.
- UART and `cool low/fast/auto/status` retained. Manual cooling lasts until auto/reboot.
- All four v0.1.5 TDDP/TSDP initialization/receive-disable patches and boot messages
  retained. Easy Smart discovery/configuration remains disabled; use the known-IP UI.

The v0.1.3 patch was too late: the outer handler could already substitute `Unauth`.
v0.1.6 changes the outer prologue at file `0x34e48`, with exact raw method/target
checks. Other requests replay the displaced instructions and continue stock code.
[HTTP trace, rationale and verification](../../docs/HTTP-AUTH.md).

## Integrity and checks

Size **1,013,324 bytes**; CRC32 **8c15e140** over `[0x10,0xf7000)`.
SHA-256:

```text
239a0127fa9ddbb72e55da992ca79c46cb9435888f7c23a82f08e42718a8ad46
```

```powershell
Get-FileHash C:\tmp\SwitchLens-SG1218MPE-V5-v0.1.6.bin -Algorithm SHA256
```

[Successful CI run](https://github.com/adsdevdoo/switchlens-sg1218/actions/runs/39144589077),
tested source `f3481b37b0decf54317c8b8f6193fd7f745934d7`; [provenance](validation.json).

| Check | Result and scope |
| --- | --- |
| Static/package | Input/output hashes, CRC, allowed modifications, ELF layout, source hashes; 108,484 bytes padding remain |
| [Raw HTTP/auth](anonymous-http-test-results.json) | 9 test methods with case matrices: original parser, outer auth gate, session isolation, admin GET/POST, aliases/methods, failure and v0.1.5 control |
| [JSON target](target-test-results.json) | 11 passed: complete schema/18 ports, metrics, streaming errors, stack/ABI and integrity |
| [UART/cooling](manual-cooling-test-results.json) | 6 passed |
| [Service disabling](security-test-results.json) | 5 passed |
| [Scheduler/boot staging](release-path-test-results.json) | 4 passed |
| Host/sanitizer | 9 host tests passed normally and under sanitizers; MIB checks passed |
| Physical switch | Not performed; owner installs and checks |

MIPS tests use synthetic sockets/MMIO. Panel/collector interleaving is tested,
not real TCP concurrency, IRQ timing or sustained PoE load. Stock login/admin
renderers are trapped at entry; auth decisions execute. SRAM snapshots detect
net changes, not every intermediate write; static paths contain no session stores.

## Install and verify on Windows

1. Check the hash, then upload this BIN through the existing Firmware Upgrade page.
   Keep normal power during upgrade. This BIN is not a complete SPI backup.
2. After boot, log out of the web panel and run without any authentication:

   ```powershell
   curl.exe --connect-timeout 5 --max-time 15 -D - http://192.168.1.3/stats.json
   ```

   Require JSON, `Content-Type: application/json`, build v0.1.6 and no `Set-Cookie`.
3. Log in to the panel on host A. On host B **with another source IP**, save
   [Test-AnonymousStats.ps1](https://github.com/adsdevdoo/switchlens-sg1218/releases/download/v0.1.6/Test-AnonymousStats.ps1)
   to `C:\tmp` and run:

   ```powershell
   powershell -NoProfile -File C:\tmp\Test-AnonymousStats.ps1 -Switch 192.168.1.3 -Count 60 -IntervalSeconds 2
   ```

   Navigate panel pages during polling: they must work without another login.
   Reports and last JSON go to `C:\tmp`. Administrative URLs from B must remain
   login-protected. The script never logs in or sends cookies.
4. Check UART `cool status` reports v0.1.6, disabled-service boot messages,
   cooling commands and normal ports/PoE. Session expiry still applies normally;
   statistics must not keep an idle panel session alive.

Report observations in the v0.1.6 development conversation; security-audit issue #1 is separate.

## Reproduce

With the compiler recorded in the manifest and `requirements-dev.txt`:

```bash
python3 tools/build_firmware.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --uart-cli --cooling-cli --anonymous-stats --output build-v016
python3 tests/test_anonymous_http.py --build build-v016
```

The [validation workflow](../../.github/workflows/validate-anonymous-stats.yml)
contains the remaining checks. Old versions and tags were not overwritten.
