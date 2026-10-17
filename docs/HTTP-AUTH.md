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
