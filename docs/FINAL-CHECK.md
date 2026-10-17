**English** | [Русский](FINAL-CHECK.ru.md)

# Final offline review of v0.1.1

17 October 2026; reviewed BIN from commit `35030053d838aefb860b5dd5088d4ff1db210740`.
**No failures in the checks performed; BIN unchanged.** This is the reader edition
of the pre-hardware report. [Original frozen release artifact](../releases/v0.1.1-experimental-uart/FINAL-CHECK.md).
Later boot, UART help and JSON were verified on hardware:
[test journal](evidence/2026-10-17-switchlens/README.md).

SHA-256 `27e4fce8d5c0c2999a324341cea7e96e37b1c0561e8d6a3218705b32b7aeee71`.

## Integrity

The public GitHub Raw download matched the archive byte-for-byte. Repackaging
in a separate directory produced the same BIN. Size 1,013,324 bytes; CRC32
`5c6abcf2` over `[0x10,0xf7000)`. Header bytes after CRC and tail from `0xf7000`
match the vendor image. JSON payload matches v0.1.0 and its source hashes match
the stored manifest. Ten bytes differ from v0.1.0 within two UART instructions
and the CRC field. The 12,120 changed bytes versus stock all lie in the allowed
CRC, HTTP hooks, UART hooks and payload regions. Original dump/vendor/earlier
release files are unchanged.

| Check | Result |
| --- | --- |
| UART prompt, Enter, help/?, unknown/no-input cases and reproduction | 6/6 |
| Stock HTTP routing/session, JSON, errors, memory/stack and CRC | 10/10 |
| Stock scheduler, shared UART/HTTP RAM and two boot paths | 4/4 |
| Host JSON serializer | 9/9 |
| MIB mapping, overflow/errors and bounded retries | PASS |
| AddressSanitizer/UndefinedBehaviorSanitizer host checks | PASS; LeakSanitizer disabled |

Scheduler `0xbfc2df8c` invokes the registered UART callback. Three sequential
help → GET cycles share synthetic RAM and preserve 18-port JSON, permitted RAM
changes and register restoration. Physical interrupts/devices are not modeled.

## Boot-path check

Executed original SPI function at file `0x1898`, RAM `0xbf0031a0`, and original
CRC function `0xbf002ebc`. Initial state: active header zeroed, staged BIN at
`0xb4100000`, matching the traced web-upgrade path. Flash initialization/mode,
copying and diagnostic output are modeled, not real SPI writes.

The new BIN passes header/CRC checks, requests a 1,013,324-byte copy to
`0xb4008000` and reaches runtime entry `0xb4008010`. The model preserves the
bootloader and SPI `[0x1fc000,0x200000)`. A one-byte staging corruption is rejected
before copy. This covers one traced branch, not every boot/recovery path;
runtime after entry and physical SignCheck were not executed by that test.

## Reproduce

```bash
python3 tools/build_uart_diagnostic.py --output build-final-check
python3 tests/test_uart_console.py --build build-final-check
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-final-check
python3 tests/test_release_paths.py
make test
ASAN_OPTIONS=detect_leaks=0 make sanitize
```

Results: [UART](../releases/v0.1.1-experimental-uart/uart-test-results.json),
[HTTP](../releases/v0.1.1-experimental-uart/target-test-results.json),
[extra paths](../releases/v0.1.1-experimental-uart/release-path-test-results.json).
At review time web installation, full boot and physical UART were outstanding;
the later hardware record now confirms those initial functions. Loaded PoE,
IRQ-stack stress, extended operation and recovery remain unverified.
