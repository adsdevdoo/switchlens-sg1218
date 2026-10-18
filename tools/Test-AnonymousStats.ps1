param(
    [string]$Switch = '192.168.1.3',
    [int]$Count = 60,
    [int]$IntervalSeconds = 2,
    [string]$OutputDirectory = 'C:\tmp',
    [string]$ExpectedBuild = 'v0.1.6'
)
$ErrorActionPreference = 'Stop'
if ($Count -lt 1 -or $Count -gt 10000 -or $IntervalSeconds -lt 1) { throw 'Invalid count/interval' }
# This checker never logs in, sends credentials, or keeps a cookie jar.
function Read-Anonymous([string]$Path) {
    $request = [System.Net.HttpWebRequest]::Create('http://' + $Switch + $Path)
    $request.Method = 'GET'
    $request.AllowAutoRedirect = $false
    $request.UseDefaultCredentials = $false
    $request.PreAuthenticate = $false
    $request.CookieContainer = $null
    $request.KeepAlive = $false
    $request.Timeout = 15000
    $request.ReadWriteTimeout = 15000
    $response = $null
    try {
        try { $response = $request.GetResponse() }
        catch [System.Net.WebException] {
            if ($null -eq $_.Exception.Response) { throw }
            $response = $_.Exception.Response
        }
        $reader = New-Object IO.StreamReader($response.GetResponseStream())
        try { $body = $reader.ReadToEnd() } finally { $reader.Dispose() }
        [pscustomobject]@{
            status = [int]$response.StatusCode
            type = $response.ContentType
            build = $response.Headers['X-SwitchLens-Build']
            sets_cookie = ($null -ne $response.Headers['Set-Cookie'])
            body = $body
        }
    } finally { if ($null -ne $response) { $response.Dispose() } }
}
$null = New-Item -ItemType Directory -Force -Path $OutputDirectory
$rows = New-Object 'System.Collections.Generic.List[object]'
$errorsFound = New-Object 'System.Collections.Generic.List[string]'
$runId = [guid]::NewGuid().ToString('N')
Write-Host 'No login or cookies. Keep using the web panel on ANOTHER IP during this run.'
Write-Host 'To check the no-session case, run once after logging out, then log in for a second run.'
for ($i=1; $i -le $Count; $i++) {
    try {
        $r = Read-Anonymous '/stats.json'
        if ($r.status -ne 200 -or $r.type -notmatch '^application/json\b') { throw 'Expected HTTP 200 application/json' }
        if ($r.build -cne $ExpectedBuild) { throw "Unexpected build: $($r.build)" }
        if ($r.sets_cookie) { throw 'Stats response set a cookie' }
        $d = $r.body | ConvertFrom-Json
        if ($d.schema_version -ne 1 -or @($d.ports).Count -ne 18) { throw 'Wrong JSON schema version or port count' }
        if ((@($d.ports | ForEach-Object { $_.port }) -join ',') -cne ((1..18) -join ',')) { throw 'Wrong port numbering' }
        [IO.File]::WriteAllText((Join-Path $OutputDirectory "stats-$runId.json"), $r.body, [Text.UTF8Encoding]::new($false))
        $rows.Add([pscustomobject]@{ sample=$i; utc=[DateTime]::UtcNow.ToString('o'); result='PASS'; build=$r.build; ports=18; sets_cookie=$false })
        Write-Host "$i/$Count PASS $($r.build), 18 ports, no Set-Cookie"
    } catch {
        $errorsFound.Add($_.Exception.Message)
        $rows.Add([pscustomobject]@{ sample=$i; utc=[DateTime]::UtcNow.ToString('o'); result='FAIL'; error=$_.Exception.Message })
        Write-Warning $_.Exception.Message
    }
    if ($i -lt $Count) { Start-Sleep -Seconds $IntervalSeconds }
}
$checks = New-Object 'System.Collections.Generic.List[object]'
# Read-only URLs only. Never probe reboot/update/settings CGI writes on hardware.
foreach ($path in @('/stats.json?x=1','/stats.jsonx','/SystemInfoRpm.htm','/ConfigRpm.htm','/fwupgradephase0.htm','/SystemRebootRpm.htm')) {
    try {
        $r = Read-Anonymous $path
        $isStats = $r.type -match '^application/json\b'
        $login = $r.body -match '(?i)logon\.cgi|H_P_SSID|username|window\.parent\.location|login'
        $denial = $r.status -in @(301,302,303,307,308,401,403)
        $pass = (-not $isStats) -and ($login -or $denial)
        $checks.Add([pscustomobject]@{ path=$path; status=$r.status; no_json=(-not $isStats); login_or_denial=($login -or $denial); result=$(if($pass){'PASS'}else{'REVIEW'}) })
        if (-not $pass) { $errorsFound.Add("Review anonymous response for $path") }
    } catch { $errorsFound.Add($_.Exception.Message) }
}
$report = [ordered]@{
    build=$ExpectedBuild; target=$Switch; utc=[DateTime]::UtcNow.ToString('o')
    credentials_sent=$false; cookie_jar_used=$false
    samples=$rows.ToArray(); negative_checks=$checks.ToArray(); errors=$errorsFound.ToArray()
    browser_session_preserved='OWNER_MUST_CONFIRM_ON_OTHER_IP'
    limits='Read-only LAN HTTP checks. Full schema is checked in CI; this script checks version and port structure. Browser continuity and natural session expiry require owner observation.'
}
$out = Join-Path $OutputDirectory "anonymous-stats-$runId.json"
[IO.File]::WriteAllText($out, ($report | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
Write-Host "Saved: $out"
Write-Host 'Confirm the panel still opens pages without another login; record the collector and browser source IPs.'
if ($errorsFound.Count) { throw "$($errorsFound.Count) failed/unconfirmed checks; see report" }
