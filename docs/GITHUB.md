# Репозиторий GitHub

Проект: **SwitchLens**.
Репозиторий: [adsdevdoo/switchlens-sg1218](https://github.com/adsdevdoo/switchlens-sg1218).

Описание:
`Experimental firmware for TP-Link TL-SG1218MPE V5 with a read-only JSON API for port counters, PoE telemetry, and system information.`

## Получение исходников

Архив `SwitchLens-v0.1.0-experimental.zip` содержит готовую папку
`switchlens-sg1218/`: рабочие файлы, каталог `.git`, всю историю коммитов,
ветку `main`, тег `v0.1.0-experimental`, четыре фото в README и собранный BIN.
Распакуйте папку целиком в удобное место. Git bundle и дополнительное
восстановление не требуются. `git init`, `git clone`, `git add` и `git commit`
для первой отправки выполнять не нужно: всё уже закоммичено.
В готовом архиве `origin` указывает на
`git@github.com:adsdevdoo/switchlens-sg1218.git`.

### Windows, PuTTY и Pageant

Оставьте Pageant запущенным с нужным ключом. В PowerShell:

```powershell
cd .\switchlens-sg1218
.\push-windows.cmd
```

Скрипт ищет `plink.exe` в `PATH` и обычных папках установки PuTTY,
на время своего запуска задаёт `GIT_SSH_COMMAND` и `GIT_SSH_VARIANT=plink`,
использует ключ из Pageant и выполняет `git push -u --follow-tags origin main`.
Аннотированный тег версии отправляется вместе с веткой.
Глобальные настройки Git и сам Pageant не меняются; force-push не используется.
Если PuTTY установлен в другую папку, добавьте её в `PATH` текущего терминала.

Если SSH для Git уже настроен так же, как в вашем другом рабочем проекте,
можно обойтись без скрипта:

```powershell
cd .\switchlens-sg1218
git remote set-url origin git@github.com:adsdevdoo/switchlens-sg1218.git
git push -u --follow-tags origin main
```

При первом подключении проверьте предложенный ключ сервера по
[документации GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints).
Если GitHub уже содержит другие коммиты и push отклонён, не используйте
`--force`: сначала нужно получить и объединить историю.

**Проверено по документации:** PuTTY описывает `GIT_SSH_COMMAND` для Git
и параметр `-agent` для Pageant; Git поддерживает вариант `plink`.
Источники: [PuTTY, глава 7](https://the.earth.li/~sgtatham/putty/0.85/htmldoc/Chapter7.html),
[Git: ssh.variant](https://git-scm.com/docs/git-config#Documentation/git-config.txt-sshvariant).
Сам Windows-скрипт в Linux-среде подготовки не выполнялся; успешный push
на компьютере владельца пока не проверен.

### После первой загрузки на GitHub

```bash
git clone git@github.com:adsdevdoo/switchlens-sg1218.git
cd switchlens-sg1218
```

Если GitHub запрашивает вход, авторизуйтесь на своей машине через GitHub CLI
или установленный менеджер учётных данных. Не передавайте токены, cookies
или пароли в чат и не добавляйте их в файлы проекта.

## Содержимое

В Git находятся исходники, скрипты сборки, схема JSON, синтетические примеры,
исследовательские отчёты, тесты, документация и разрешённые владельцем фото
платы в `docs/images/`. Вся история проекта сохраняется.

Исходные официальные BIN, полные SPI-дампы, UART-журналы, скриншоты сетевых
настроек и реальные сетевые данные остаются вне репозитория.
По запросу владельца собранный экспериментальный BIN включён в
`releases/v0.1.0-experimental/` с контрольными суммами и манифестом.
Не добавляйте другие стендовые файлы и дампы из `bench/`.

Проверенный офлайн статус и ограничения: [FIRMWARE](FIRMWARE.md).
Загрузка и работа экспериментального образа на устройстве ещё не проверены.

## CI

Workflow [host-tests.yml](../.github/workflows/host-tests.yml) проверяет
host-прототип, не скачивает прошивку и не подключается к устройствам.
Результаты запусков доступны во вкладке
[Actions](https://github.com/adsdevdoo/switchlens-sg1218/actions).

Успешный CI не подтверждает работу прошивки на реальном коммутаторе.

Исключение по прямому запросу владельца от 2026-10-17: исходный экспорт
GD25Q16B включён без изменений в `backups/original/2026-10-17/`
вместе с SHA-256 и результатами первичной проверки. Остальные дампы
не добавляются автоматически.
