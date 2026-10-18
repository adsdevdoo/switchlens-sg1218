#requires -Version 5.1
<#
Owner-authorized, single-switch factory-MAC write/readback probe.
This ERASES a factory flash sector and rewrites its first 194 bytes.
Restoration is best effort, not guaranteed. No reboot/reset is sent.
A changed factory readback is evidence of a write path, not a power-cycle test.
Use only on the owner's isolated TL-SG1218MPE V5 with a verified backup.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SwitchIP,
    [Parameter(Mandatory=$true)][string]$ExpectedMac,
    [Parameter(Mandatory=$true)][string]$BackupPath,
    [string]$OutputPath = (Join-Path (Get-Location).Path 'tddp-write-readback-result.json'),
    [switch]$Execute
)
$ErrorActionPreference = 'Stop'
$ip = [Net.IPAddress]::Parse($SwitchIP)
if ($ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) { throw 'IPv4 required.' }
$octets = $ip.GetAddressBytes()
$private = ($octets[0] -eq 10) -or
    (($octets[0] -eq 172) -and ($octets[1] -ge 16) -and ($octets[1] -le 31)) -or
    (($octets[0] -eq 192) -and ($octets[1] -eq 168))
if (-not $private) { throw 'Only one RFC1918 IPv4 target is supported.' }
$expected = ($ExpectedMac -replace '[:-]', '').ToUpperInvariant()
if ($expected -notmatch '^[0-9A-F]{12}$') { throw 'Invalid ExpectedMac.' }
[byte[]]$original = New-Object byte[] 6
for ($i=0; $i -lt 6; $i++) { $original[$i] = [Convert]::ToByte($expected.Substring(2*$i,2),16) }
if (($original[0] -band 1) -ne 0) { throw 'Expected MAC must be unicast.' }

[byte[]]$backup = [IO.File]::ReadAllBytes($BackupPath)
if ($backup.Length -ne 2097424) { throw 'Backup size mismatch.' }
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = [BitConverter]::ToString($sha.ComputeHash($backup)).Replace('-','').ToLowerInvariant() }
finally { $sha.Dispose() }
if ($hash -ne 'b80e10d5fb75ee2d4d8a45dba305090fe204d521c96d24202876273959589a87') {
    throw 'Backup SHA-256 does not match the reviewed original export.'
}
for ($i=0; $i -lt 6; $i++) {
    if ($backup[0x1FC000+$i] -ne $original[$i]) { throw 'Backup MAC does not match ExpectedMac.' }
}
for ($i=0x1FC0C2; $i -lt 0x1FD000; $i++) {
    if ($backup[$i] -ne 255) { throw 'Unexpected non-FF data outside preserved factory buffer.' }
}
[byte[]]$temporary = $original.Clone()
# Set the locally-administered bit; retain unicast, and ensure a different value.
$temporary[0] = [byte]($temporary[0] -bor 2)
if ($temporary[0] -eq $original[0]) { $temporary[5] = [byte]($temporary[5] -bxor 1) }
function MacText([byte[]]$value) { return [BitConverter]::ToString($value).Replace('-',':') }
$originalText = MacText $original
$temporaryText = MacText $temporary
$fullOutput = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $fullOutput) { throw 'Output already exists; choose a new OutputPath to preserve evidence.' }
$report = [ordered]@{
    probe='SwitchLens single-target factory MAC write/readback v1'
    started_utc=[DateTime]::UtcNow.ToString('o')
    target=$ip.ToString(); authentication_supplied=$false
    backup_sha256=$hash; original_mac=$originalText; temporary_mac=$temporaryText
    write_attempted=$false; changed_readback_confirmed=$false
    restoration='NOT_NEEDED'; reboot_sent=$false; power_cycle_persistence_tested=$false
    result='PREFLIGHT_ONLY'; steps=@(); errors=@()
}
function Save-Checkpoint {
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $fullOutput -Encoding UTF8
}
Save-Checkpoint
if (-not $Execute) {
    $report | ConvertTo-Json -Depth 8
    Write-Host 'Preflight only; no network packets. Add -Execute to perform the authorized write/readback.'
    return
}
$script:transaction = Get-Random -Minimum 1 -Maximum 60000
$udp = $null
$writeAttempted = $false
$readAfter = $null

function Exchange {
    param([int]$Opcode, [int]$ReplyOpcode, [int]$ReplyType, [int]$ReplyLength,
          [string]$Phase, [byte[]]$Payload = @())
    $script:transaction++
    [byte[]]$packet = New-Object byte[] (12+$Payload.Length)
    $packet[0]=1; $packet[1]=[byte]$Opcode; $packet[2]=1
    $packet[7]=[byte]$Payload.Length
    $packet[8]=[byte]($script:transaction -shr 8)
    $packet[9]=[byte]($script:transaction -band 255)
    if ($Payload.Length -gt 0) { [Array]::Copy($Payload,0,$packet,12,$Payload.Length) }
    $step = [ordered]@{
        phase=$Phase; time_utc=[DateTime]::UtcNow.ToString('o')
        request_hex=[BitConverter]::ToString($packet).Replace('-','')
        result='SEND_PENDING'; reply_hex=$null; mac=$null; ignored_datagrams=0
    }
    $report.steps += $step
    # Log intent before transmission. The first checkpoint was already checked writable.
    try { Save-Checkpoint } catch { Write-Warning ('Checkpoint failed: '+$_.Exception.Message) }
    $dest = [Net.IPEndPoint]::new($ip,1040)
    [void]$udp.Send($packet,$packet.Length,$dest)
    $step.result='NO_MATCHING_REPLY_INCONCLUSIVE'
    $clock=[Diagnostics.Stopwatch]::StartNew()
    while ($clock.ElapsedMilliseconds -lt 5000) {
        $udp.Client.ReceiveTimeout=[int][Math]::Max(1,5000-$clock.ElapsedMilliseconds)
        $peer=[Net.IPEndPoint]::new([Net.IPAddress]::Any,0)
        try { [byte[]]$reply=$udp.Receive([ref]$peer) }
        catch [Net.Sockets.SocketException] {
            if ($_.Exception.SocketErrorCode -eq [Net.Sockets.SocketError]::TimedOut) { break }
            throw
        }
        $match=$peer.Address.Equals($ip) -and ($peer.Port -eq 1040) -and
            ($reply.Length -eq (12+$ReplyLength))
        if ($match) {
            $match=($reply[0] -eq 1) -and ($reply[1] -eq $ReplyOpcode) -and
                ($reply[2] -eq $ReplyType) -and ($reply[4] -eq 0) -and
                ($reply[5] -eq 0) -and ($reply[6] -eq 0) -and
                ($reply[7] -eq $ReplyLength) -and
                ($reply[8] -eq $packet[8]) -and ($reply[9] -eq $packet[9])
        }
        if (-not $match) { $step.ignored_datagrams++; continue }
        $step.reply_hex=[BitConverter]::ToString($reply).Replace('-','')
        if ($reply[3] -eq 0) {
            $step.result='MATCHING_REPLY'
            if ($Opcode -eq 15) { $step.mac=MacText ([byte[]]$reply[12..17]) }
        } else { $step.result='DEVICE_ERROR_'+$reply[3] }
        break
    }
    try { Save-Checkpoint } catch { Write-Warning ('Checkpoint failed: '+$_.Exception.Message) }
    return $step
}
try {
    $udp=[Net.Sockets.UdpClient]::new([Net.Sockets.AddressFamily]::InterNetwork)
    $udp.Client.ExclusiveAddressUse=$true
    $udp.Client.Bind([Net.IPEndPoint]::new([Net.IPAddress]::Any,61000))
    $before=Exchange 15 15 2 6 'read_before'
    if ($before.result -ne 'MATCHING_REPLY') {
        $null=Exchange 12 4 1 0 'control_exchange'
        $before=Exchange 15 15 2 6 'read_after_control'
    }
    if (($before.result -ne 'MATCHING_REPLY') -or ($before.mac -ne $originalText)) {
        throw 'Live MAC missing or unexpected; stopped before any flash write.'
    }
    $report.result='WRITE_PENDING'
    $report.write_attempted=$true
    Save-Checkpoint
    $writeAttempted=$true
    $null=Exchange 6 6 2 0 'write_temporary' $temporary
    $readAfter=Exchange 15 15 2 6 'read_temporary'
    if ($readAfter.mac -eq $temporaryText) {
        $report.changed_readback_confirmed=$true
        $report.result='CHANGED_FACTORY_READBACK_WITHOUT_CREDENTIALS_CONFIRMED'
    } elseif ($readAfter.mac -eq $originalText) {
        $report.result='NO_MAC_CHANGE_OBSERVED'
    } else { $report.result='WRITE_OUTCOME_INCONCLUSIVE' }
}
catch {
    $report.errors += $_.Exception.Message
    if (-not $report.changed_readback_confirmed) { $report.result='ERROR_INCONCLUSIVE' }
}
finally {
    if ($writeAttempted -and ($null -ne $udp)) {
        if (($null -ne $readAfter) -and ($readAfter.mac -eq $originalText)) {
            $report.restoration='ORIGINAL_ALREADY_READ_BACK; NO_EXTRA_WRITE'
        } else {
            $report.restoration='RESTORE_ATTEMPT_PENDING'
            try {
                # Exactly one restoration write; no automatic repeated flash writes.
                $null=Exchange 6 6 2 0 'restore_original' $original
                $restored=Exchange 15 15 2 6 'read_restored'
                if ($restored.mac -eq $originalText) {
                    $report.restoration='ORIGINAL_MAC_READBACK_CONFIRMED'
                } else { $report.restoration='NOT_CONFIRMED; DO_NOT_REBOOT' }
            } catch {
                $report.restoration='ERROR; DO_NOT_REBOOT'
                $report.errors += $_.Exception.Message
            }
        }
    }
    if ($null -ne $udp) { $udp.Close() }
    $report['finished_utc']=[DateTime]::UtcNow.ToString('o')
    $json=$report | ConvertTo-Json -Depth 8
    Write-Output $json
    try {
        $json | Set-Content -LiteralPath $fullOutput -Encoding UTF8
        Write-Host ('Saved: '+$fullOutput)
    } catch { Write-Warning ('Save failed; retain the console JSON: '+$_.Exception.Message) }
}
