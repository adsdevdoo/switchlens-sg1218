**English** | [Русский](HTTP-AUTH.ru.md)

# HTTP authentication and automated statistics

## v0.1.6: statistics without a web session

Only the exact **`GET /stats.json`** is public. It needs no login, password,
cookie, token or preliminary request. The web panel and administrative endpoints
retain the stock form login, `H_P_SSID` cookie and client-IP checks.

```powershell
curl.exe --connect-timeout 5 --max-time 15 -D - http://192.168.1.3/stats.json
```

Use `curl` on Linux/macOS. Do not add `-u`, `-b`, `-c`, an Authorization header,
or a login request. Expect HTTP 200, `Content-Type: application/json`,
`Cache-Control: no-store`, `X-SwitchLens-Build: v0.1.6`, complete schema-1 JSON
and 18 ports. The response must not contain `Set-Cookie`.

Statistics do not create/replace a session, change its cookie/IP, or refresh its
expiry timer, even when requested from the browser's IP with a valid cookie.
A collector on another IP may poll while the owner uses the panel. Natural panel
session expiry still applies; polling does not keep the panel logged in.

Query strings, case variants, suffixes, encoded variants and other methods do
not receive the exception. Examples: `/stats.json?x=1`, `/Stats.json`,
`/stats.json/`, `/stats.jsonx`, `POST /stats.json`, `HEAD /stats.json`.
They continue through the stock handler; this is not a global auth bypass.
Telemetry is readable by any host that can reach the management HTTP port.
Keep that interface on the intended management network.

## Collection and validation

Start with one request every 30 seconds and no overlapping collector requests;
this is a conservative starting interval, not a measured maximum rate.
Accept only complete JSON matching [the schema](../schema/stats.schema.json).
HTTP 200 with login HTML is a failure. Record transport/JSON errors as missing
data, not zero counters. Do not attempt automatic login to repair a stats error.

Counter values remain decimal strings; use arbitrary-precision integers.
Preserve `null` as unavailable. Compute rates from successive successful samples
and collector elapsed time; discard intervals where counters decrease or the
switch reboots. `system.firmware_version` remains the stock vendor string;
identify this build by `X-SwitchLens-Build` or UART `cool status`.

## Why v0.1.3 did not work

v0.1.3 changed an inner login-path comparison at file `0x33770`, inside router
`0xbfc3b740`. Its caller `0xbfc3ce48` had already rejected a different client IP
and substituted `Unauth`. Its tests started after that gate. The owner's switch
therefore still returned the login form. v0.1.4 removed the ineffective patch.
v0.1.5 added TDDP/TSDP disabling, but retained session-required statistics.

v0.1.6 replaces only the first eight bytes at outer entry `0xbfc3ce48` with a
trampoline. It checks parsed method/path **and the raw `GET /stats.json ` prefix**,
then invokes the existing guarded JSON handler before any session check or timer
refresh. Nonmatching requests replay the two displaced prologue instructions and
resume the original function at `0xbfc3ce50`. The inner auth block is unchanged.

Raw checks matter: parser `0xbf01d05c` stores a query-stripped path at request+8
and recognizes GET using three bytes. Checking only those fields would admit
queries or `GETX`. Raw buffer and target pointers at +0x88/+0x8c are checked too.
The stock same-IP path refreshes timer `0xbf011670` to 600; the anonymous path
never executes that store. No new global RAM flag is used.

## Evidence and limits

[Raw HTTP regression](../tests/test_anonymous_http.py) executes the original
MIPS parser and patched outer callback, with stock inner auth on rejected paths.
It compares session cookie/flag/IP/timer and restricts all SRAM changes to stack
and HTTP output buffers. Cases cover no session, another IP, absent/wrong/valid
cookies, panel/collector interleaving, admin GET/POST, aliases/methods, failures,
and the archived v0.1.5 negative control.

Sockets and MMIO are synthetic. Interleaving is not proof of real simultaneous
TCP/interrupt behavior. No installation or LAN test of v0.1.5 or v0.1.6 is claimed.
The owner's last confirmed installed build was v0.1.4.

## Short Windows hardware check

1. Install the [v0.1.6 BIN](../releases/v0.1.6/README.md) through the stock web
   upgrade page. Confirm build header/UART version after reboot.
2. Log out of the panel. Run the command above without any cookie; require JSON.
3. Log in to the panel on host A. On **host B with a different source IP**, run
   [Test-AnonymousStats.ps1](../tools/Test-AnonymousStats.ps1):

   ```powershell
   powershell -NoProfile -File C:\tmp\Test-AnonymousStats.ps1 -Switch 192.168.1.3 -Count 60 -IntervalSeconds 2
   ```

4. During polling, navigate/refresh panel pages on A. It must stay usable without
   another login. The script checks version/JSON/no Set-Cookie and read-only
   negative URLs, saving reports and the last sample under `C:\tmp`.
5. From B, administrative pages must still display login/denial. To check that
   polling does not extend expiry, let a separate panel session sit idle for the
   normal device timeout while B keeps polling; verify it expires normally.

A second terminal on A does not establish the different-IP case. Record both
source IPs, boot markers (`HTTPD ready; TSDP disabled`, `TDDP disabled`), panel
continuity, UART `cool low/fast/auto/status`, switching and PoE observations in
the v0.1.6 development conversation. Keep security-audit issue #1 separate.
