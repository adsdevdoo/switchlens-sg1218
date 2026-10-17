# Репозиторий GitHub

Проект: **SwitchLens**.
Репозиторий: [adsdevdoo/switchlens-sg1218](https://github.com/adsdevdoo/switchlens-sg1218).

Описание:
`Experimental firmware for TP-Link TL-SG1218MPE V5 with a read-only JSON API for port counters, PoE telemetry, and system information.`

## Получение исходников

Если получен архив `SwitchLens-github-source.zip`, распакуйте его так, чтобы
папка `switchlens-sg1218` оказалась в `~/work/`. В актуальном архиве это уже
полный Git-репозиторий с каталогом `.git`, веткой `main` и историей коммитов.
Повторные `git init`, `git add` и `git commit` для первого push не нужны.
Не путайте этот архив с GitHub Download ZIP: последний не содержит `.git`.

### Windows, PuTTY и Pageant

Оставьте Pageant запущенным с нужным ключом. В PowerShell:

```powershell
cd ~/work/switchlens-sg1218
.\push-windows.cmd
```

Скрипт ищет `plink.exe` в `PATH` и обычных папках установки PuTTY,
на время своего запуска задаёт `GIT_SSH_COMMAND` и `GIT_SSH_VARIANT=plink`,
использует ключ из Pageant и выполняет обычный `git push -u origin main`.
Глобальные настройки Git и сам Pageant не меняются; force-push не используется.
Если PuTTY установлен в другую папку, добавьте её в `PATH` текущего терминала.

Если SSH для Git уже настроен так же, как в вашем другом рабочем проекте,
можно обойтись без скрипта:

```powershell
cd ~/work/switchlens-sg1218
git remote set-url origin git@github.com:adsdevdoo/switchlens-sg1218.git
git push -u origin main
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

Оригинальные и модифицированные BIN, полные SPI-дампы, UART-журналы,
скриншоты сетевых настроек и реальные сетевые данные остаются вне репозитория.
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
