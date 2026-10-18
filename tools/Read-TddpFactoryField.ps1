#requires -Version 5.1
# Read-only factory-field probe: MAC read, optional control exchange, 40-byte read.
# No flash/configuration writes, reset or reboot. RAM protocol state may change.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SwitchIP,
    [Parameter(Mandatory=$true)][string]$ExpectedMac,
    [Parameter(Mandatory=$true)][string]$BackupPath,
    [ValidateRange(500,10000)][int]$TimeoutMs = 3000,
    [string]$OutputPath = (Join-Path (Get-Location).Path 'tddp-field40-result.json')
)
$ErrorActionPreference = 'Stop'
$ip = [Net.IPAddress]::Parse($SwitchIP)
if ($ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) { throw 'IPv4 required.' }
$expected = ($ExpectedMac -replace '[:-]', '').ToUpperInvariant()
if ($expected -notmatch '^[0-9A-F]{12}$') { throw 'Invalid ExpectedMac.' }
[byte[]]$backup = [IO.File]::ReadAllBytes($BackupPath)
if ($backup.Length -ne 2097424) { throw 'Unexpected backup size.' }
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = [BitConverter]::ToString($sha.ComputeHash($backup)).Replace('-','').ToLowerInvariant() }
finally { $sha.Dispose() }
if ($hash -ne 'b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87') {
    throw 'Backup SHA-256 mismatch.'
}
$backupMac = [BitConverter]::ToString([byte[]]$backup[0x1FC000..0x1FC005]).Replace('-','')
if ($backupMac -ne $expected) { throw 'ExpectedMac does not match the backup.' }
[byte[]]$archived = $backup[0x1FC096..0x1FC0BD]
$archivedHex = [BitConverter]::ToString($archived).Replace('-','')
$archivedAscii = ($archived | ForEach-Object {
    if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { '.' }
}) -join ''
$fullOutput = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $fullOutput) { throw 'Output exists; use a new OutputPath.' }
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
        source_port=$null; mac=$null; expected_mac_match=$null; payload_hex=$null; payload_ascii=$null
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
        $matches = $peer.Address.Equals($ip) -and ($peer.Port -eq 1040) -and ($reply.Length -eq (12+$PayloadLength))
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
        if ($PayloadLength -gt 0) {
            [byte[]]$payload = $reply[12..(11+$PayloadLength)]
            $step.payload_hex = [BitConverter]::ToString($payload).Replace('-','')
            $step.payload_ascii = ($payload | ForEach-Object {
                if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { '.' }
            }) -join ''
        }
        break
    }
    return $step
}

$report = [ordered]@{
    probe='SwitchLens factory field40 read-only v1'
    timestamp_utc=[DateTime]::UtcNow.ToString('o')
    target=$ip.ToString(); authentication_supplied=$false
    configuration_write_sent=$false; reboot_sent=$false
    transient_protocol_state_may_change=$true
    backup_sha256=$hash; field_offset='0x1fc096'; field_bytes=40
    archived_hex=$archivedHex; archived_ascii=$archivedAscii
    live_hex=$null; live_ascii=$null; matches_archived=$null
    result='NOT_RUN'; steps=@()
}
function Save-Checkpoint {
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $fullOutput -Encoding UTF8
}
Save-Checkpoint
$udp=$null
try {
    $udp=[Net.Sockets.UdpClient]::new([Net.Sockets.AddressFamily]::InterNetwork)
    $udp.Client.ExclusiveAddressUse=$true
    $udp.Client.Bind([Net.IPEndPoint]::new([Net.IPAddress]::Any,61000))
    $transaction=Get-Random -Minimum 1 -Maximum 60000
    $before=Invoke-TddpStep $udp 15 15 2 6 $transaction 'mac_before'
    $report.steps += $before
    Save-Checkpoint
    if ($before.result -ne 'MATCHING_REPLY') {
        $control=Invoke-TddpStep $udp 12 4 1 0 ($transaction+1) 'control_exchange'
        $report.steps += $control
        Save-Checkpoint
        $before=Invoke-TddpStep $udp 15 15 2 6 ($transaction+2) 'mac_after_control'
        $report.steps += $before
        Save-Checkpoint
    }
    if (($before.result -ne 'MATCHING_REPLY') -or ($before.expected_mac_match -ne $true)) {
        throw 'Live MAC missing or unexpected; field read not sent.'
    }
    $field=Invoke-TddpStep $udp 13 13 2 40 ($transaction+3) 'read_field40'
    $report.steps += $field
    if ($field.result -eq 'MATCHING_REPLY') {
        $report.live_hex=$field.payload_hex
        $report.live_ascii=$field.payload_ascii
        $report.matches_archived=($field.payload_hex -eq $archivedHex)
        $report.result='FACTORY_FIELD40_READ_WITHOUT_CREDENTIALS_CONFIRMED'
    } else { $report.result='FIELD40_NO_MATCHING_REPLY_INCONCLUSIVE' }
}
catch {
    $report.result='LOCAL_OR_NETWORK_ERROR_INCONCLUSIVE'
    $report['error']=$_.Exception.Message
}
finally {
    if ($null -ne $udp) { $udp.Close() }
    $report['finished_utc']=[DateTime]::UtcNow.ToString('o')
    $json=$report | ConvertTo-Json -Depth 8
    Write-Output $json
    try {
        $json | Set-Content -LiteralPath $fullOutput -Encoding UTF8
        Write-Host ('Saved: '+$fullOutput)
    } catch { Write-Warning ('Save failed; retain console JSON: '+$_.Exception.Message) }
}
