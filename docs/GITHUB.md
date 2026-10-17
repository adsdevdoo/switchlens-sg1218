**English** | [Русский](GITHUB.ru.md)

# GitHub repository workflow

Project: **SwitchLens** — [adsdevdoo/switchlens-sg1218](https://github.com/adsdevdoo/switchlens-sg1218).
Suggested description: `Working firmware for TP-Link TL-SG1218MPE V5 with a read-only JSON API, port counters, PoE telemetry, system information and UART CLI.`

## Current workflow

The owner requests direct repository updates through the connected GitHub plugin;
manual archive transfer is unnecessary. Publish against the current main head
with a concurrency check, then verify the resulting commit/tree. English reader
documentation is the default; each guide links its Russian counterpart.

```bash
git clone https://github.com/adsdevdoo/switchlens-sg1218.git
cd switchlens-sg1218
```

SSH alternative:

```bash
git clone git@github.com:adsdevdoo/switchlens-sg1218.git
```

Authenticate locally using the user's configured Git tools. Do not put tokens,
cookies or passwords in chat or project files. If the remote has newer commits,
fetch and reconcile history; do not use force push to bypass a conflict.

## Historical Windows/PuTTY helper

The original `SwitchLens-v0.1.0-experimental.zip` handoff contained a complete
repository including `.git`, main, version tag, photographs and BIN. That archive
is historical, not the current source of truth. It required no git init or
initial commit; the remote was `git@github.com:adsdevdoo/switchlens-sg1218.git`.

The optional Windows helper uses `%USERPROFILE%\.ssh\adsdev.ppk`:

```powershell
cd .\switchlens-sg1218
.\push-windows.cmd
# Or choose a key explicitly:
.\push-windows.cmd "C:\path\to\key.ppk"
```

It finds plink in PATH/common PuTTY locations, sets GIT_SSH_COMMAND and
GIT_SSH_VARIANT=plink only for the process, and uses `-l git -noagent -noshare -i`
with the selected key. `SWITCHLENS_SSH_KEY` is another override. Missing keys stop
before push. Encrypted keys may prompt locally. It pushes main and annotated
tags with `git push -u --follow-tags origin main`, without force. Pageant/shared
connections are bypassed for this process; global Git/Pageant settings are unchanged.
Add a custom PuTTY installation to the current terminal PATH if necessary.

If SSH is already configured:

```powershell
git remote set-url origin git@github.com:adsdevdoo/switchlens-sg1218.git
git push -u --follow-tags origin main
```

On first connection verify the host key against
[GitHub fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints).
Supporting documentation: [PuTTY chapter 7](https://the.earth.li/~sgtatham/putty/0.85/htmldoc/Chapter7.html),
[Git ssh.variant](https://git-scm.com/docs/git-config#Documentation/git-config.txt-sshvariant).
The Windows helper was not run in the Linux preparation environment; that is
separate from successful publication through the GitHub plugin.

## Contents and publication scope

Sources, build scripts, schema, synthetic examples, analysis, tests, paired docs,
versioned BINs and owner-authorized board/evidence files are tracked. Original
vendor ZIP/BIN/PDF packages live in [vendor](../vendor/tp-link/tl-sg1218mpe-v5/README.md).
Do not automatically add other bench dumps/logs.

Authorized exceptions: original GD25Q16B export; full stock boot text and earlier
UART images; the current successful test's selected messages, eight screenshots
and two full JSON replies, including this bench's IP/MAC. Details are in
[CONTRIBUTING](../CONTRIBUTING.md). These do not authorize future sessions/secrets.

[Working-firmware evidence](evidence/2026-10-17-switchlens/README.md) is separate
from [offline implementation checks](FIRMWARE.md). Historical tag/BIN names
remain intact so existing downloads and checksums stay valid.

## CI and releases

[host-tests.yml](../.github/workflows/host-tests.yml) checks the host prototype;
it does not connect to hardware. Results are in [Actions](https://github.com/adsdevdoo/switchlens-sg1218/actions).
The publication workflow creates the existing v0.1.1 release from checked assets
and refuses to silently replace mismatched published attachments. Ordinary doc
updates do not change the firmware. CI success alone is not hardware evidence.
