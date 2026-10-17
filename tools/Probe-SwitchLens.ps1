#requires -Version 5.1
<#
One-device diagnostic: unauthenticated HTTP GETs and one TDDP MAC-read query.
No credentials, discovery broadcast, handshake, configuration/flash writes,
reboot, reset, or firewall changes. TSDP is not probed.
The stock MAC-read handler can update transient TDDP state 0 -> 1; send failure
can set it to 2. This is not a completely side-effect-free protocol operation.
No UDP response is INCONCLUSIVE, not proof of a closed port or a secure device.
Packet semantics checked against stock V5 build 20230616 in MIPS emulation.
PowerShell execution on the physical Windows host remains to be verified.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SwitchIP,
    [string]$ExpectedMac = '',
    [ValidateRange(500,10000)][int]$TimeoutMs = 3000,
    [string]$OutputPath = (Join-Path (Get-Location).Path 'switchlens-probe.json')
)
$ErrorActionPreference = 'Stop'
$ip = [System.Net.IPAddress]::Parse($SwitchIP)
if ($ip.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw 'An IPv4 address is required.'
}
$expected = ($ExpectedMac -replace '[:-]', '').ToUpperInvariant()
if ($expected -and $expected -notmatch '^[0-9A-F]{12}$') { throw 'Invalid ExpectedMac.' }

function Read-WebSummary([string]$Path) {
    $response = $null
    $reader = $null
    try {
        $request = [System.Net.HttpWebRequest]::Create(('http://{0}{1}' -f $ip, $Path))
        $request.Method = 'GET'
        $request.Proxy = $null
        $request.AllowAutoRedirect = $false
        $request.UseDefaultCredentials = $false
        $request.Timeout = $TimeoutMs
        $request.ReadWriteTimeout = $TimeoutMs
        try { $response = $request.GetResponse() }
        catch [System.Net.WebException] {
            if ($null -eq $_.Exception.Response) { throw }
            $response = $_.Exception.Response
        }
        $reader = [System.IO.StreamReader]::new($response.GetResponseStream())
        $buffer = New-Object char[] 4096
        $count = $reader.Read($buffer, 0, $buffer.Length)
        $prefix = -join $buffer[0..([Math]::Max(0,$count-1))]
        $kind = 'other'
        if ($prefix -match '(?is)<html|<!doctype|<form') { $kind = 'html' }
        if ($prefix -match '^\s*\{') { $kind = 'json-prefix-only' }
        # Do not print/store response bodies, cookies, passwords or telemetry.
        return [ordered]@{
            path = $Path
            status = [int]$response.StatusCode
            build = [string]$response.Headers['X-SwitchLens-Build']
            content_type = [string]$response.ContentType
            response_kind = $kind
            model_name_seen = [bool]($prefix -match 'TL-SG1218MPE')
            login_form_seen = [bool]($prefix -match '(?i)logon\.cgi|name\s*=\s*["'']?password')
        }
    }
    catch { return [ordered]@{ path=$Path; error=$_.Exception.Message } }
    finally {
        if ($null -ne $reader) { $reader.Dispose() }
        if ($null -ne $response) { $response.Close() }
    }
}

$report = [ordered]@{
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    target = $ip.ToString()
    authentication_supplied = $false
    http = @()
    tddp = [ordered]@{
        destination_port=1040; local_reply_port=61000; opcode=15
        request='single MAC read; no handshake'
        result='NOT_RUN'; received_mac=$null; expected_mac_match=$null
        note='No response is inconclusive. Replies do not prove flash-write access.'
    }
    tsdp = 'NOT_TESTED'
}

Write-Host ('Target: {0}. No login or configuration writes.' -f $ip)
foreach ($path in @('/', '/stats.json')) { $report.http += Read-WebSummary $path }

$udp = $null
try {
    $udp = [System.Net.Sockets.UdpClient]::new([System.Net.Sockets.AddressFamily]::InterNetwork)
    $udp.Client.ExclusiveAddressUse = $true
    # Firmware replies to fixed port 61000, not an arbitrary ephemeral port.
    # Close Easy Smart Utility if it already occupies this local port.
    $udp.Client.Bind([System.Net.IPEndPoint]::new([System.Net.IPAddress]::Any,61000))
    [byte[]]$packet = @(1,15,1,0,0,0,0,0,0,0,0,0)
    $transaction = Get-Random -Minimum 1 -Maximum 65536
    $packet[8] = [byte]($transaction -shr 8)
    $packet[9] = [byte]($transaction -band 255)
    $destination = [System.Net.IPEndPoint]::new($ip,1040)
    [void]$udp.Send($packet,$packet.Length,$destination)
    $report.tddp.result = 'NO_MATCHING_REPLY_INCONCLUSIVE'
    $clock = [System.Diagnostics.Stopwatch]::StartNew()
    while ($clock.ElapsedMilliseconds -lt $TimeoutMs) {
        $udp.Client.ReceiveTimeout = [int][Math]::Max(1,$TimeoutMs-$clock.ElapsedMilliseconds)
        $peer = [System.Net.IPEndPoint]::new([System.Net.IPAddress]::Any,0)
        try { $reply = $udp.Receive([ref]$peer) }
        catch [System.Net.Sockets.SocketException] {
            if ($_.Exception.SocketErrorCode -eq [System.Net.Sockets.SocketError]::TimedOut) { break }
            throw
        }
        if (-not $peer.Address.Equals($ip)) { continue }
        if ($reply.Length -ne 18) { continue }
        if ($reply[0] -ne 1 -or $reply[1] -ne 15 -or $reply[2] -ne 2 -or $reply[3] -ne 0) { continue }
        if ($reply[4] -ne 0 -or $reply[5] -ne 0 -or $reply[6] -ne 0 -or $reply[7] -ne 6) { continue }
        if ($reply[8] -ne $packet[8] -or $reply[9] -ne $packet[9]) { continue }
        $mac = ($reply[12..17] | ForEach-Object { $_.ToString('X2') }) -join ':'
        $report.tddp.result = 'MAC_READ_REPLY_WITHOUT_CREDENTIALS'
        $report.tddp.received_mac = $mac
        if ($expected) { $report.tddp.expected_mac_match = (($mac -replace ':','') -eq $expected) }
        $report.tddp['source_port'] = $peer.Port
        break
    }
}
catch {
    $report.tddp.result = 'LOCAL_OR_NETWORK_ERROR_INCONCLUSIVE'
    $report.tddp['error'] = $_.Exception.Message
}
finally { if ($null -ne $udp) { $udp.Close() } }

$json = $report | ConvertTo-Json -Depth 6
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output $json
Write-Host ('Saved: {0}' -f [System.IO.Path]::GetFullPath($OutputPath))
Write-Host 'No reply can mean state gating, filtering/firewall, loss, or disabled service.'
Write-Host 'This probe does NOT establish a password bypass or factory-write vulnerability.'
