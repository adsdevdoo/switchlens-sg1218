**English** | [Русский](README.ru.md)

# SwitchLens v0.1.5 — disable TDDP/TSDP

[**BIN**](https://github.com/adsdevdoo/switchlens-sg1218/raw/refs/heads/main/releases/v0.1.5/SwitchLens-SG1218MPE-V5-v0.1.5.bin) · [SHA256SUMS](SHA256SUMS) · [Manifest](build-manifest.json)

```text
SHA-256 b2617a639869cf5ca0ef7b953b321f0625f3a1af3c6aab8d1a37a7ffa3dd6a7d
Bytes   1013324
CRC32   ff2c1e25
```

The stock TDDP (UDP 1040) and TSDP (UDP 29808) management services are
disabled: initialization creates no sockets and both receive callbacks return
immediately. TP-Link's utility can no longer discover/manage the switch through
these services. Use the web interface at its known IP address.

Stock web login, authenticated `/stats.json`, UART and `cool low`, `cool fast`,
`cool auto`, `cool status` remain. Manual modes have no timeout; reboot restores
auto. RPM and individual fan health remain unknown.

**This closes network entry points; it is not a complete security redesign.**
The fixed RC4 key and reversible credential storage remain in the stock codec
for compatibility with existing configuration/login. HTTP still lacks TLS.
An intentional backdoor or universal absence of hidden accounts is not proven.
[Findings, addresses and audit limits](../../research/SECURITY-AUDIT.md).

**All 26 MIPS checks pass; this exact BIN has not been tested on hardware.**
11 HTTP/JSON, 6 fan-control, 4 boot/CRC/scheduler and 5 service-disable checks.
Sockets, flash and peripherals are mocked. These are not physical network,
recovery or endurance tests.

Install only on TL-SG1218MPE(UN) V5.0, 20230616 base, through Firmware Upgrade.
This is an update image, not a full SPI dump. Old versions and originals remain.
After installation check login, JSON, UART and normal switching/PoE behavior.
`cool status` and the `X-SwitchLens-Build` HTTP header should report `v0.1.5`.
Boot messages now say `HTTPD ready; TSDP disabled` and `TDDP disabled`.
The earlier `tddp_tsdp_dhcp_igmp trap cpu set` message configures ASIC traps and
may remain; it does not demonstrate that the disabled services are running.

[Authenticated metrics collection](../../docs/HTTP-AUTH.md).

## Reproduce

`requirements-dev.txt`, MIPS GCC/binutils.

```bash
python3 tools/build_firmware.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --uart-cli --cooling-cli --output build-v015
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-v015
python3 tests/test_manual_cooling.py --build build-v015
python3 tests/test_release_paths.py --build build-v015
python3 tests/test_security.py --build build-v015
python3 tools/audit_security.py
```
