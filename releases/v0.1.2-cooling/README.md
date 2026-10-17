**English** | [Русский](README.ru.md)

# SwitchLens v0.1.2 — cooling diagnostics

Diagnostic build with short `cool` commands, bounded GPIO27 hold, automatic return
and a `cooling` object in `/stats.json`. **24 MIPS tests pass; this new build has
not yet been installed on hardware.** v0.1.1 remains hardware-verified working
firmware. Historical BINs are preserved.

[**Download BIN**](https://github.com/adsdevdoo/switchlens-sg1218/raw/refs/heads/main/releases/v0.1.2-cooling/SwitchLens-SG1218MPE-V5-v0.1.2-cooling.bin)
· [SHA256SUMS](SHA256SUMS) · [Build manifest](build-manifest.json)

```text
SHA-256 07bcc33628b01af5687054758fb67d32a800b2eac1025d0c3cf0afd073ea9dc2
Bytes   1013324
CRC32   cc484259
```

TL-SG1218MPE(UN) V5.0 only, based on 20230616. This is a stock web-update image, not a full SPI dump.

[Commands, implementation and limits](../../docs/COOLING-CONTROL.md)
· [JSON API](../../docs/JSON-API.md#cooling-v012)

```text
cool status
cool test 0
cool auto
cool test 1
cool auto
```

Enter one line at a time and observe between commands; this is not a paste-all script. Start with status. Return after 100 raw ticks; duration in seconds is uncalibrated. A repeated test cannot extend the limit. `cool auto` cancels immediately. `0/1` are GPIO levels, not speed names. RPM and fan health remain null.

Timeout requires a running timer and main loop. Test state is not written to flash; a power cycle clears it if the console stalls. Stock control thresholds, bootloader, HTTP authentication and existing telemetry fields are retained.

## Checks

- [Cooling/CLI: 10](cooling-test-results.json)
- [HTTP/JSON: 10](target-test-results.json)
- [Scheduler/boot staging: 4](release-path-test-results.json)
- [Host serializer/MIB, ASan/UBSan](host-test-results.json)
- [stats.synthetic.json](stats.synthetic.json) — synthetic example, not device data

Payload: 16632 bytes; audited FF remaining: 108744 bytes.
No new persistent RAM is allocated. Changes are limited to payload, listed hooks and CRC.

## Reproduce

```bash
python3 -m pip install -r requirements-dev.txt
# Debian/Ubuntu: gcc-mips-linux-gnu binutils-mips-linux-gnu
make generated
python3 tools/build_firmware.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --uart-cli --cooling-cli --output build-cooling
python3 tests/test_cooling.py --build build-cooling
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-cooling
python3 tests/test_release_paths.py --build build-cooling
make test
make sanitize
```

Exact compiler/linker versions and source hashes are in the manifest. Here ASan/UBSan ran with `ASAN_OPTIONS=detect_leaks=0`: LeakSanitizer cannot run under ptrace.
