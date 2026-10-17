**English** | [Русский](README.ru.md)

# SwitchLens v0.1.3 — public statistics and manual fan modes

**Superseded / correction:** the owner confirmed boot and manual fan commands, but unauthenticated JSON still requires login. The claimed public access below was not achieved. v0.1.4 removes the ineffective exception and restores stock authentication. The original BIN and reports are retained as historical evidence. [v0.1.4](../v0.1.4/README.md).

Built on the working SwitchLens firmware. This exact BIN passes 21 MIPS checks
and host serializer/MIB plus ASan/UBSan; installation on the owner's hardware
is pending. Earlier v0.1.1 boot/JSON and v0.1.2 fan-speed observations remain valid
for those builds, not a claim that this new image has already been flashed.

[**Download BIN**](https://github.com/adsdevdoo/switchlens-sg1218/raw/refs/heads/main/releases/v0.1.3-public-stats/SwitchLens-SG1218MPE-V5-v0.1.3-public-stats.bin) · [SHA256SUMS](SHA256SUMS) · [Manifest](build-manifest.json)

```text
SHA-256 3ffeaface23a7da9856854337caae5f89fd0e0df21145d833275e921e6da43e4
Bytes   1013324
CRC32   260bf144
```

Only TL-SG1218MPE(UN) V5.0, stock base 20230616. Web-upgrade image, not a full SPI dump.
Install through the existing Firmware Upgrade page. Then open `/stats.json` without
logging in; the response header is `X-SwitchLens-Build: v0.1.3-public-stats`.
The stock System Info version string is unchanged.

## Changes

- Exact `GET /stats.json` no longer requires a session or credentials. Other
  administrative pages and POST handlers retain stock authentication. Anyone
  with network access to this endpoint can read its telemetry, including IP/MAC
  and port configuration. The endpoint remains read-only.
- `cool low`: shared lower-speed output (GPIO27=1), until another command or reboot.
- `cool fast`: shared higher-speed output (GPIO27=0), until another command or reboot.
- `cool auto`: restore the stock PoE-based hysteresis using the current load.
- `cool status`: show policy, shared output mode, GPIO26 and diagnostic registers.
- No `cool test` command and no 100-tick timeout. Manual modes can be switched
  directly; they do not follow PoE load until `cool auto`. No flash setting is saved;
  startup initializes the stock automatic state.
- `cooling.speed_mode` is `low`, `fast` or null for invalid state/mux/direction.
  `cooling.mode` is `auto`, `manual` or `invalid`. These report commands, not measured
  RPM. Legacy `test_level`, `remaining_ticks`, `test_limit_ticks` are null.
- FAN indicator handling is unchanged. GPIO26 still drives the stock indicator
  decision; it is not per-fan RPM or a verified health flag. `fan_rpm` and `fan_status`
  remain null. GPIO27 affects both fans, as observed by the owner.

## Implementation and checks

The new session exception patches the strcmp call at file offset `0x33770`.
It accepts only method 1 (GET) with both router path representations exactly
`/stats.json`; otherwise it performs the original login-path comparison. No
session flag or cookie is changed. The subsequent stock GET router and existing
JSON hooks are reused. No public fan-control endpoint is added.

Manual overrides use the existing RAM word `0xbf014840`:
`0xd8000000 | saved_auto_state<<25 | level<<24`. The stock controller continues
power aggregation and preserves this tagged value. GPIO output uses the existing
read/modify/write helper, preserving other bits. `auto` restores the saved state
and recomputes from current power. No newly allocated persistent RAM or bootloader
changes. Register writes are rejected while a manual override is active.

- [HTTP/JSON: 11 checks](target-test-results.json), including missing-session GET,
  protected admin/POST/near-matching paths, unchanged session RAM and read-only output.
- [Manual cooling: 6 checks](manual-cooling-test-results.json), including operation
  across tick wrap and changing PoE, direct mode changes, auto hysteresis and null data.
- [Scheduler and boot CRC paths: 4 checks](release-path-test-results.json).
- [Host checks](host-test-results.json). [Synthetic JSON](stats.synthetic.json).

Emulation mocks peripherals/network/flash boundaries; it does not establish actual
installation, sustained device operation or physical recovery.

## Reproduce

Dependencies: `requirements-dev.txt`, MIPS GCC/binutils. Regenerate fields with
`make generated`, then:

```bash
python3 tools/build_firmware.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --uart-cli --cooling-cli --public-stats --output build-public
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-public
python3 tests/test_manual_cooling.py --build build-public
python3 tests/test_release_paths.py --build build-public
make test
ASAN_OPTIONS=detect_leaks=0 make sanitize
```
