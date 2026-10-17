**English** | [Русский](HTTP-AUTH.ru.md)

# HTTP authentication and automated statistics

The switch uses a form login plus the `H_P_SSID` session cookie and a client-IP
check. This is not HTTP Basic/Digest, Bearer or an API key. Login and collection
must originate from the same client IP. Transferring a browser cookie to a server
with another IP does not establish a valid session there.

## Request sequence

The embedded login page at stock file offset `0x95ecc` submits a form using
`POST /logon.cgi`. Fields include `username`, `password`, `logon=Login` and an
empty `cpassword` on ordinary login. The firmware emits `Set-Cookie` and the
`H_P_SSID=tplink_` prefix. No JavaScript password hash was found in that form.

Example for Windows PowerShell (`curl.exe`; replace the placeholders locally):

```powershell
curl.exe -c cookies.txt --data-urlencode "username=YOUR_USERNAME" --data-urlencode "password=YOUR_PASSWORD" --data "logon=Login&cpassword=" http://192.168.1.3/logon.cgi
curl.exe -b cookies.txt http://192.168.1.3/stats.json
```

On Linux/macOS use `curl`. These request fields were read from the firmware;
the complete command sequence has not yet been verified against the owner's
unit. Validate that the result is JSON with the expected schema and 18 ports;
HTML with HTTP 200 is a login failure, not a valid sample. On expiry, perform
normal login again and replace the cookie jar. No session duration is assumed.
The URL uses plain HTTP, so the password/cookie are not encrypted in transit.
Do not commit real credentials or cookies. The telemetry handler only reads.

## Continuous collection

Run login and polling in the same process or on the same host, with a stable
source IP. Keep one cookie jar per switch. A successful HTTP status alone does
not prove login: accept a session only after an authenticated `/stats.json`
request returns a complete, valid metrics document.

1. POST the form above and save the response cookies. Do not send the password
   on every statistics request; subsequent GETs carry the session cookie.
2. GET `/stats.json` with that jar. Set a connection timeout and a total request
   timeout; for example, 5 and 15 seconds. These are collector settings, not
   measured firmware limits.
3. Parse the entire response as JSON and validate it against
   [stats.schema.json](../schema/stats.schema.json). Require `schema_version: 1`
   and exactly 18 ports numbered 1–18. Do not accept a login HTML page, a
   truncated body or an unexpected object as a sample.
4. If the switch returns the login page or denies authorization, discard that
   response, clear the old jar, log in once, and retry the GET once. If this
   still fails, report collection failure and wait before retrying. Do not
   create an unlimited login loop. For a network timeout or malformed JSON,
   report the transport/data error rather than assuming the password expired.
5. Start with one request every 30 seconds, without overlapping requests. This
   is a conservative starting interval, not a tested maximum polling rate.
   Reuse the session until the switch stops accepting it. After a reboot, IP
   change or rejected session, establish a new session normally.

Example GET after login, saving response headers and body separately:

```powershell
curl.exe --connect-timeout 5 --max-time 15 -b cookies.txt -c cookies.txt -D stats.headers -o stats.json http://192.168.1.3/stats.json
```

On Linux/macOS replace `curl.exe` with `curl`. `-b` loads cookies and `-c`
persists any updated cookies. This command only downloads a response: the
collector must still perform the validation and retry policy above. Do not
publish `cookies.txt` or `stats.headers`, which may contain session cookies.
Avoid logging the login request body. Store credentials and the jar in files
readable only by the collector account. Collect over a trusted management
network: this firmware serves HTTP without transport encryption.

Use one collector as the session owner and let dashboards read its stored
metrics. The inspected firmware uses global session state; concurrent logins
from a browser or another collector may interfere. Multi-client session
behavior has not been verified on hardware.

## Turning samples into metrics

Record a collector timestamp for each accepted sample. Keep the last successful
sample time and a separate collection-success flag. An authentication/network
failure is missing data, not zero traffic, zero PoE power or a healthy fan.

- Counter values are decimal strings: parse with Python `int` or JavaScript
  `BigInt`, not floating-point conversion. Compute traffic rates from two valid
  samples: `bits_per_second = 8 * (new_bytes - old_bytes) / elapsed_seconds`.
  Use the collector's monotonic elapsed time; the firmware's raw tick scale is
  unconfirmed. If a counter decreases or the device reboots, discard that rate
  interval and establish a new baseline instead of producing a negative rate.
- Preserve `null` as unavailable. Do not replace it with zero. Fan RPM and
  individual fan health remain unknown; `cooling.speed_mode` reports the
  commanded shared speed mode, not measured RPM or proof that both fans spin.
- `system.firmware_version` retains the vendor version string. The
  `X-SwitchLens-Build` response header identifies the SwitchLens build; keep it
  alongside samples when available.

The form fields and session checks are established from firmware inspection;
the automated login/poll/relogin workflow still needs verification on the unit.

## v0.1.3 correction

The owner confirmed v0.1.3 boots and accepts manual fast/low commands, but an
unauthenticated statistics request still displays the login form. The previous
public-endpoint claim was incorrect.

The attempted patch changed the login-path comparison at `0x33770` inside
router `0xbfc3b740`. However, its caller at `0xbfc3ce48` checks the client IP
against RAM `0xbf018df4` and can pass the `Unauth` route before the inner router
runs. The v0.1.3 test entered the inner router directly and missed this gate.

v0.1.4 removes that hook, its helper, build flag and build definition entirely.
The session-check block `0x33740..0x33804` and outer handler
`0x34e48..0x34f58` match the stock image byte-for-byte. New MIPS coverage enters
the outer handler and checks: valid cookie/same IP succeeds; wrong cookie,
different IP and no active session do not reach JSON. These are CPU tests with
synthetic request data, not a full network/login test.

v0.1.3 is retained only as historical evidence; use v0.1.4 for normal stock
authentication. No further authentication bypass is requested or included.
