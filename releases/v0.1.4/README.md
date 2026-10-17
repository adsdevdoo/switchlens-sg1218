**English** | [Русский](README.ru.md)

# SwitchLens v0.1.4 — stock authentication restored

The ineffective v0.1.3 authentication exception has been removed completely.
Manual `cool low`, `cool fast`, `cool auto`, `cool status` and `cooling.speed_mode`
are retained. Low/fast have no timeout and reset to auto on reboot. No `cool test`.

[**Download BIN**](https://github.com/adsdevdoo/switchlens-sg1218/raw/refs/heads/main/releases/v0.1.4/SwitchLens-SG1218MPE-V5-v0.1.4.bin) · [SHA256SUMS](SHA256SUMS) · [Manifest](build-manifest.json)

```text
SHA-256 4093f2e0dfcbbbc1c0caf0ed1d9d8902de747aa41e9525840b4755004e791b93
Bytes   1013324
CRC32   45977043
```

TL-SG1218MPE(UN) V5.0, stock 20230616 base. Install through Firmware Upgrade.
`/stats.json` requires the normal login, cookie and client IP. The header is
`X-SwitchLens-Build: v0.1.4`; the stock System Info version string is unchanged.
[Authentication, curl commands and v0.1.3 error analysis](../../docs/HTTP-AUTH.md).

**21 MIPS checks pass; this exact image has not yet been installed on hardware.**
[HTTP/JSON: 11](target-test-results.json), [manual control: 6](manual-cooling-test-results.json),
[scheduler/boot CRC: 4](release-path-test-results.json). The auth blocks are
byte-identical to stock. GPIO control, unrelated bits, cookie/IP acceptance and
rejection paths are covered. [Synthetic response](stats.synthetic.json).
Socket/flash/peripherals are mocked; physical recovery and sustained load remain unverified.

The earlier hardware confirmations concern v0.1.1 and v0.1.2/v0.1.3. This release
is built on the working firmware; it is not labelled hardware-verified before installation.
Historical BINs are preserved. No bootloader, vendor image or SPI dump is modified.

## Reproduce

Use `requirements-dev.txt`, MIPS GCC/binutils, then:

```bash
python3 tools/build_firmware.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --uart-cli --cooling-cli --output build-v014
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-v014
python3 tests/test_manual_cooling.py --build build-v014
python3 tests/test_release_paths.py --build build-v014
```
