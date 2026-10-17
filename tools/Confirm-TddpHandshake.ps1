#requires -Version 5.1
<#
Single-device TDDP evidence probe for an owner-authorized switch.
Sends at most three unicast requests: MAC read, control exchange if needed,
then MAC read. No credentials, configuration/flash writes, reset or reboot.
The control exchange and MAC read can change transient TDDP state in RAM.
This establishes only handshake/read behavior, NEVER physical flash-write access.
No reply is inconclusive. Close Easy Smart Utility if it occupies UDP 61000.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SwitchIP,
    [string]$ExpectedMac = '',
    [ValidateRange(500,10000)][int]$TimeoutMs = 3000,
    [string]$OutputPath = (Join-Path (Get-Location).Path 'tddp-handshake-result.json')
)
$ErrorActionPreference = 'Stop'
$ip = [System.Net.IPAddress]::Parse($SwitchIP)
if ($ip.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw 'An IPv4 address is required.'
}
$expected = ($ExpectedMac -replace '[:-]', '').ToUpperInvariant()
if ($expected -and $expected -notmatch '^[0-9A-F]{12}$') { throw 'Invalid ExpectedMac.' }

function Invoke-TddpStep {
    param([System.Net.Sockets.UdpClient]$Client, [int]$Opcode,
          [int]$ReplyOpcode, [int]$ReplyType, [int]$PayloadLength,
          [int]$Transaction, [string]$Name)
    [byte[]]$packet = @(1,0,1,0,0,0,0,0,0,0,0,0)
    $packet[1] = [byte]$Opcode
    $packet[8] = [byte]($Transaction -shr 8)
    $packet[9] = [byte]($Transaction -band 255)
    $step = [ordered]@{
        phase=$Name; request_opcode=$Opcode; transaction=$Transaction
        request_hex=[BitConverter]::ToString($packet).Replace('-','')
        result='NO_MATCHING_REPLY_INCONCLUSIVE'; reply_hex=$null
        source_port=$null; mac=$null; expected_mac_match=$null
        ignored_datagrams=0
    }
    $destination = [System.Net.IPEndPoint]::new($ip,1040)
    [void]$Client.Send($packet,$packet.Length,$destination)
    $clock = [System.Diagnostics.Stopwatch]::StartNew()
    while ($clock.ElapsedMilliseconds -lt $TimeoutMs) {
        $Client.Client.ReceiveTimeout = [int][Math]::Max(1,$TimeoutMs-$clock.ElapsedMilliseconds)
        $peer = [System.Net.IPEndPoint]::new([System.Net.IPAddress]::Any,0)
        try { [byte[]]$reply = $Client.Receive([ref]$peer) }
        catch [System.Net.Sockets.SocketException] {
            if ($_.Exception.SocketErrorCode -eq [System.Net.Sockets.SocketError]::TimedOut) { break }
            throw
        }
        $matches = $peer.Address.Equals($ip) -and ($reply.Length -eq (12+$PayloadLength))
        if ($matches) {
            $matches = ($reply[0] -eq 1) -and ($reply[1] -eq $ReplyOpcode) -and
                ($reply[2] -eq $ReplyType) -and ($reply[3] -eq 0) -and
                ($reply[4] -eq 0) -and ($reply[5] -eq 0) -and
                ($reply[6] -eq 0) -and ($reply[7] -eq $PayloadLength) -and
                ($reply[8] -eq $packet[8]) -and ($reply[9] -eq $packet[9])
        }
        if (-not $matches) { $step.ignored_datagrams++; continue }
        $step.result = 'MATCHING_REPLY'
        $step.reply_hex = [BitConverter]::ToString($reply).Replace('-','')
        $step.source_port = $peer.Port
        if ($Opcode -eq 15) {
            $step.mac = ($reply[12..17] | ForEach-Object { $_.ToString('X2') }) -join ':'
            if ($expected) { $step.expected_mac_match = (($step.mac -replace ':','') -eq $expected) }
        }
        break
    }
    return $step
}

$report = [ordered]@{
    probe='SwitchLens TDDP handshake/read v1'
    timestamp_utc=[DateTime]::UtcNow.ToString('o'); target=$ip.ToString()
    authentication_supplied=$false; configuration_write_sent=$false
    transient_protocol_state_may_change=$true
    destination_port=1040; local_reply_port=61000
    result='NOT_RUN'; steps=@()
    proves_flash_write_access=$false
}
$udp = $null
Write-Host ('Target: {0}. TDDP control exchange and MAC read only; no flash/configuration writes.' -f $ip)
try {
    $udp = [System.Net.Sockets.UdpClient]::new([System.Net.Sockets.AddressFamily]::InterNetwork)
    $udp.Client.ExclusiveAddressUse = $true
    $udp.Client.Bind([System.Net.IPEndPoint]::new([System.Net.IPAddress]::Any,61000))
    $transaction = Get-Random -Minimum 1 -Maximum 65534
    $before = Invoke-TddpStep $udp 15 15 2 6 $transaction 'mac_read_before'
    $report.steps += $before
    if ($before.result -eq 'MATCHING_REPLY') {
        $report.result = 'MAC_READ_WITHOUT_CREDENTIALS_ALREADY_AVAILABLE'
    } else {
        $handshake = Invoke-TddpStep $udp 12 4 1 0 ($transaction+1) 'control_exchange'
        $report.steps += $handshake
        $after = Invoke-TddpStep $udp 15 15 2 6 ($transaction+2) 'mac_read_after'
        $report.steps += $after
        if ($after.result -eq 'MATCHING_REPLY') {
            if ($handshake.result -eq 'MATCHING_REPLY') {
                $report.result = 'HANDSHAKE_AND_MAC_READ_WITHOUT_CREDENTIALS_CONFIRMED'
            } else {
                $report.result = 'MAC_READ_CONFIRMED_HANDSHAKE_REPLY_NOT_OBSERVED'
            }
        } elseif ($handshake.result -eq 'MATCHING_REPLY') {
            $report.result = 'HANDSHAKE_ONLY_CONFIRMED_MAC_READ_INCONCLUSIVE'
        } else {
            $report.result = 'NO_MATCHING_REPLY_INCONCLUSIVE'
        }
    }
}
catch {
    $report.result = 'LOCAL_OR_NETWORK_ERROR_INCONCLUSIVE'
    $report['error'] = $_.Exception.Message
}
finally { if ($null -ne $udp) { $udp.Close() } }
$json = $report | ConvertTo-Json -Depth 6
Write-Output $json
$json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host ('Saved: {0}' -f [System.IO.Path]::GetFullPath($OutputPath))
Write-Host 'No reply is inconclusive. A successful read does not prove flash-write access.'
