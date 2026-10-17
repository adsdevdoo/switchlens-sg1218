[English](README.md) | **Русский**

# SwitchLens v0.1.4 — восстановлена штатная авторизация

Неработающее исключение авторизации v0.1.3 полностью удалено. Сохранены
`cool low`, `cool fast`, `cool auto`, `cool status` и `cooling.speed_mode`.
Low/fast без таймера; перезагрузка возвращает авто. Команды `cool test` нет.

[**Скачать BIN**](https://github.com/adsdevdoo/switchlens-sg1218/raw/refs/heads/main/releases/v0.1.4/SwitchLens-SG1218MPE-V5-v0.1.4.bin) · [SHA256SUMS](SHA256SUMS) · [Манифест](build-manifest.json)

```text
SHA-256 4093f2e0dfcbbbc1c0caf0ed1d9d8902de747aa41e9525840b4755004e791b93
Bytes   1013324
CRC32   45977043
```

TL-SG1218MPE(UN) V5.0, база 20230616. Установка через Firmware Upgrade.
`/stats.json` требует штатного входа, cookie и IP клиента. Заголовок сборки —
`X-SwitchLens-Build: v0.1.4`; штатная строка System Info не изменена.
[Авторизация, команды curl и разбор ошибки v0.1.3](../../docs/HTTP-AUTH.ru.md).

**21 проверка MIPS пройдена; установка именно этого BIN на устройство пока не подтверждена.**
[HTTP/JSON: 11](target-test-results.json), [ручные режимы: 6](manual-cooling-test-results.json),
[планировщик/CRC загрузки: 4](release-path-test-results.json). Проверены побайтовая
сохранность штатных блоков авторизации, GPIO и прочих битов, допуск и отказ
по cookie/IP. [Синтетический ответ](stats.synthetic.json).
Сеть/флеш/периферия подменены; физическое восстановление и длительная нагрузка не проверены.

Прежние аппаратные подтверждения относятся к v0.1.1 и v0.1.2/v0.1.3. Это новая
сборка рабочей прошивки, а не заранее объявленная проверенной на устройстве версия.
Исторические BIN сохранены. Загрузчик, штатные образы и дамп SPI не меняются.

## Воспроизведение

Зависимости: `requirements-dev.txt`, MIPS GCC/binutils.

```bash
python3 tools/build_firmware.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --uart-cli --cooling-cli --output build-v014
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-v014
python3 tests/test_manual_cooling.py --build build-v014
python3 tests/test_release_paths.py --build build-v014
```
