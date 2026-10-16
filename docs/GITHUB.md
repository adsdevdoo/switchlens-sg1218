# Удалённый репозиторий

Имя: **SwitchLens**. Репозиторий: **switchlens-sg1218**.
Описание: `Read-only JSON telemetry research for TP-Link TL-SG1218MPE V5.0`.
Начальная видимость: private. Реальные сетевые данные и оригинальные образы
не входят в проект.

Удалённый репозиторий в рамках текущей сессии не создан: доступ к GitHub
для создания репозиториев не предоставлен. Локальный Git-проект готов.

Если создавать из архива исходников на своей машине:

```bash
cd switchlens-sg1218
git init -b main
git add .
git commit -m "Initialize SwitchLens host telemetry prototype"
gh auth login
gh repo create switchlens-sg1218 --private --source=. --remote=origin --push \
  --description "Read-only JSON telemetry research for TP-Link TL-SG1218MPE V5.0"
```

В актуальном приватном комплекте рядом с исходниками есть `bench/` с прошивкой.
Не инициализируйте Git в корне всего комплекта и не загружайте `bench/` на GitHub.
Готовый bundle содержит только исходный проект и историю, без BIN.

Для архива с историей уже достаточно распаковать `switchlens-sg1218.bundle` и:

```bash
git clone switchlens-sg1218.bundle switchlens-sg1218-restored
cd switchlens-sg1218-restored
git remote remove origin
gh auth login
gh repo create switchlens-sg1218 --private --source=. --remote=origin --push \
  --description "Read-only JSON telemetry research for TP-Link TL-SG1218MPE V5.0"
```

`origin` после clone указывает на локальный bundle; команда remove убирает
именно эту локальную ссылку перед назначением GitHub remote.
Не передавайте токены, cookies или пароли в чат. Авторизацию выполняйте в GitHub.
Проверено по [документации GitHub CLI](https://cli.github.com/manual/gh_repo_create):
`--private` задаёт видимость, `--source` использует локальную репу, `--push`
отправляет коммиты; без OWNER используется аккаунт текущей авторизации.

CI использует официальные
[actions/checkout](https://github.com/actions/checkout) и
[actions/setup-python](https://github.com/actions/setup-python), v7 согласно
их документации на дату подготовки. Workflow проверяет только host-прототип,
не скачивает прошивку и не подключается к устройствам.
