[English](README.md) | **Русский**

# SwitchLens v0.1.5 — отключение TDDP/TSDP

[**BIN**](https://github.com/adsdevdoo/switchlens-sg1218/raw/refs/heads/main/releases/v0.1.5/SwitchLens-SG1218MPE-V5-v0.1.5.bin) · [SHA256SUMS](SHA256SUMS) · [Manifest](build-manifest.json)

```text
SHA-256 b2617a639869cf5ca0ef7b953b321f0625f3a1af3c6aab8d1a37a7ffa3dd6a7d
Bytes   1013324
CRC32   ff2c1e25
```

Отключены штатные UDP-службы управления TDDP (1040) и TSDP (29808):
инициализация не создаёт сокеты, оба обработчика входящих сообщений сразу
возвращаются. Фирменная утилита TP-Link больше не сможет обнаруживать и
настраивать свитч через эти службы. Используйте веб-интерфейс по известному IP.

Сохранены штатный веб-вход, JSON `/stats.json` с авторизацией, UART и команды
`cool low`, `cool fast`, `cool auto`, `cool status` без таймера. Перезагрузка
возвращает автоматический режим. RPM и исправность каждого вентилятора неизвестны.

**Это ограничение сетевого доступа, а не полная переработка безопасности.**
Фиксированный RC4-ключ и обратимое хранение учётных данных остаются в штатном
кодеке для совместимости с существующей конфигурацией и входом. HTTP по-прежнему
без TLS. Намеренная закладка или универсальное отсутствие скрытых пользователей
не доказаны. [Находки, адреса и ограничения аудита](../../research/SECURITY-AUDIT.ru.md).

**Все 26 MIPS-проверок прошли; этот BIN ещё не проверен на устройстве.**
11 проверок HTTP/JSON, 6 управления вентиляторами, 4 загрузки/CRC/планировщика,
5 отключения служб. Сокеты, flash и периферия подменены в эмуляторе. Это не
проверка физической сети, восстановления или длительной работы.

Установка: только TL-SG1218MPE(UN) V5.0, база 20230616; через Firmware Upgrade.
Это файл обновления, не полный дамп SPI. Старые версии и оригиналы сохранены.
После установки проверьте веб-вход, JSON, UART и обычную работу портов/PoE.
`cool status` и HTTP-заголовок `X-SwitchLens-Build` должны показывать `v0.1.5`.
Загрузочный лог теперь сообщает `HTTPD ready; TSDP disabled` и `TDDP disabled`.
Прежний лог `tddp_tsdp_dhcp_igmp trap cpu set` относится к настройке ASIC и может
остаться: он не доказывает запуск отключённых служб.

[Как собирать метрики с авторизацией](../../docs/HTTP-AUTH.ru.md).

## Воспроизведение

`requirements-dev.txt`, MIPS GCC/binutils.

```bash
python3 tools/build_firmware.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --uart-cli --cooling-cli --output build-v015
python3 tests/test_target.py vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin --build build-v015
python3 tests/test_manual_cooling.py --build build-v015
python3 tests/test_release_paths.py --build build-v015
python3 tests/test_security.py --build build-v015
python3 tools/audit_security.py
```
