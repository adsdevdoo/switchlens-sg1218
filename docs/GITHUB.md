# Репозиторий GitHub

Проект: **SwitchLens**.
Репозиторий: [adsdevdoo/switchlens-sg1218](https://github.com/adsdevdoo/switchlens-sg1218).

Описание:
`Experimental firmware for TP-Link TL-SG1218MPE V5 with a read-only JSON API for port counters, PoE telemetry, and system information.`

## Получение исходников

```bash
git clone https://github.com/adsdevdoo/switchlens-sg1218.git
cd switchlens-sg1218
```

Если GitHub запрашивает вход, авторизуйтесь на своей машине через GitHub CLI
или установленный менеджер учётных данных. Не передавайте токены, cookies
или пароли в чат и не добавляйте их в файлы проекта.

## Содержимое

В Git находятся исходники, скрипты сборки, схема JSON, синтетические примеры,
исследовательские отчёты, тесты и документация. Вся история проекта сохраняется.

Оригинальные и модифицированные BIN, полные SPI-дампы, UART-журналы,
скриншоты и реальные сетевые данные остаются вне репозитория.
В приватном комплекте стенда прошивка находится отдельно, в `bench/`.
Не инициализируйте Git в корне всего комплекта и не добавляйте `bench/`.

Проверенный офлайн статус и ограничения: [FIRMWARE](FIRMWARE.md).
Загрузка и работа экспериментального образа на устройстве ещё не проверены.

## CI

Workflow [host-tests.yml](../.github/workflows/host-tests.yml) проверяет
host-прототип, не скачивает прошивку и не подключается к устройствам.
Результаты запусков доступны во вкладке
[Actions](https://github.com/adsdevdoo/switchlens-sg1218/actions).

Успешный CI не подтверждает работу прошивки на реальном коммутаторе.
