[English](README.md) | **Русский**

# SwitchLens v0.1.2 — cooling diagnostics

Диагностическая сборка с короткими командами `cool`, временным удержанием GPIO27,
автоматическим возвратом и блоком `cooling` в `/stats.json`. **24 MIPS-теста пройдены;
эта новая сборка ещё не испытана на устройстве.** v0.1.1 остаётся подтверждённой
рабочей прошивкой. Исторические BIN сохранены.

[**Скачать BIN**](https://github.com/adsdevdoo/switchlens-sg1218/raw/refs/heads/main/releases/v0.1.2-cooling/SwitchLens-SG1218MPE-V5-v0.1.2-cooling.bin)
· [SHA256SUMS](SHA256SUMS) · [Build manifest](build-manifest.json)

```text
SHA-256 07bcc33628b01af5687054758fb67d32a800b2eac1025d0c3cf0afd073ea9dc2
Bytes   1013324
CRC32   cc484259
```

Только TL-SG1218MPE(UN) V5.0, основа 20230616. Файл предназначен для штатного web-обновления, это не полный дамп SPI.

[Команды, устройство теста и ограничения](../../docs/COOLING-CONTROL.ru.md)
· [JSON API](../../docs/JSON-API.ru.md#cooling-v012)

```text
cool status
cool test 0
cool auto
cool test 1
cool auto
```

Вводить по одной строке и наблюдать между командами; это не скрипт для вставки целиком. Сначала status. Возврат после 100 raw-тиков, точная длительность в секундах не проверена. Повторный тест не продлевает срок. `cool auto` отменяет сразу. `0/1` — электрические уровни GPIO, не названия скоростей. RPM и здоровье вентиляторов остаются null.

Тайм-аут требует работающего таймера и главного цикла. Новый тест не сохраняется в flash; при зависшей консоли выключение/включение очищает его. Пороги штатного контроллера, загрузчик, авторизация HTTP и прежние поля статистики сохранены.

## Проверки

- [Cooling/CLI: 10](cooling-test-results.json)
- [HTTP/JSON: 10](target-test-results.json)
- [Scheduler/boot staging: 4](release-path-test-results.json)
- [Host serializer/MIB, ASan/UBSan](host-test-results.json)
- [stats.synthetic.json](stats.synthetic.json) — синтетический пример, не данные устройства

Полезная нагрузка: 16632 bytes; остаток проверенного FF: 108744 bytes.
Новая постоянная RAM не выделяется. Изменения ограничены payload, перечисленными hooks и CRC.

## Повторить сборку

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

Точные версии компилятора/линкера и SHA исходников записаны в manifest. В данной среде ASan/UBSan запускались с `ASAN_OPTIONS=detect_leaks=0`: LeakSanitizer не работает под ptrace.
