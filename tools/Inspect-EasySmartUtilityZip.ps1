# Static ZIP inventory and protocol-related strings. Does not execute archived files.
# Windows PowerShell 5.1+. No network calls and no switch access.
param(
    [string]$ZipPath = (Join-Path $env:USERPROFILE 'Downloads\EasySmartConfigurationUtility.zip'),
    [string]$OutputDirectory = (Join-Path $env:TEMP ('SwitchLens-utility-' + [guid]::NewGuid().ToString('N')))
)
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath $ZipPath -PathType Leaf)) { throw "ZIP not found: $ZipPath" }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$null = New-Item -ItemType Directory -Path $OutputDirectory -Force
$files = New-Object 'System.Collections.Generic.List[object]'
$hits = New-Object 'System.Collections.Generic.List[object]'
$ascii = [Text.Encoding]::GetEncoding(28591)
$keyword = '(?i)tddp|tsdp|factory|flash|signature|sha.?1|rsa|md5|product.?id|device.?id|unique.?id|config.?mac|config.?pin|set.?sign|sys.?init|udp|61000|1040|password|\.pdb|sendto|recvfrom|ws2_32'
$sha = [Security.Cryptography.SHA256]::Create()
$totalRead = [long]0
$archiveHash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
$archive = [IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    foreach ($entry in $archive.Entries) {
        if (!$entry.Name) { continue }
        $row = [ordered]@{
            path = $entry.FullName; bytes = $entry.Length; sha256 = $null
            status = 'NOT_READ'; pe_machine = $null; strings_truncated = $false
        }
        if ($entry.Length -gt 67108864 -or ($totalRead + $entry.Length) -gt 536870912) {
            $row.status = 'SKIPPED_SIZE_LIMIT'
            $files.Add([pscustomobject]$row)
            continue
        }
        $stream = $entry.Open()
        $memory = New-Object IO.MemoryStream
        try {
            $stream.CopyTo($memory)
            $bytes = $memory.ToArray()
        } finally { $stream.Dispose(); $memory.Dispose() }
        $totalRead += $bytes.Length
        $row.sha256 = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()
        $row.status = 'READ'
        if ($bytes.Length -ge 64 -and $bytes[0] -eq 77 -and $bytes[1] -eq 90) {
            $pe = [BitConverter]::ToInt32($bytes,60)
            if ($pe -ge 0 -and $pe -le ($bytes.Length - 6) -and
                $bytes[$pe] -eq 80 -and $bytes[$pe+1] -eq 69 -and
                $bytes[$pe+2] -eq 0 -and $bytes[$pe+3] -eq 0) {
                $row.pe_machine = ('0x{0:X4}' -f [BitConverter]::ToUInt16($bytes,$pe+4))
            }
        }
        $extension = [IO.Path]::GetExtension($entry.Name).ToLowerInvariant()
        if ($extension -in @('.exe','.dll','.ini','.cfg','.conf','.xml','.json','.txt','.properties','.config')) {
            $raw = $ascii.GetString($bytes)
            $count = 0
            foreach ($kind in @('ascii','utf16le')) {
                $pattern = if ($kind -eq 'ascii') { '[\x20-\x7E]{5,}' } else { '(?:[\x20-\x7E]\x00){5,}' }
                $match = [regex]::Match($raw,$pattern)
                while ($match.Success) {
                    $value = if ($kind -eq 'ascii') { $match.Value } else { $match.Value.Replace([string][char]0,'') }
                    if ($value -match $keyword) {
                        if ($count -ge 2000 -or $hits.Count -ge 20000) {
                            $row.strings_truncated = $true
                            break
                        }
                        $hits.Add([pscustomobject]@{
                            file = $entry.FullName
                            offset_hex = ('0x{0:X}' -f $match.Index)
                            encoding = $kind
                            text = $value.Substring(0,[Math]::Min(2000,$value.Length))
                            original_characters = $value.Length
                        })
                        $count++
                    }
                    $match = $match.NextMatch()
                }
            }
        }
        $files.Add([pscustomobject]$row)
    }
} finally { $archive.Dispose(); $sha.Dispose() }
$report = [ordered]@{
    probe = 'SwitchLens static utility ZIP inspection v1'
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    archive_name = [IO.Path]::GetFileName($ZipPath)
    archive_sha256 = $archiveHash
    archive_executed = $false
    device_contacted = $false
    limitations = 'Keyword strings are leads, not proof of implemented commands. No disassembly or recursive nested-archive analysis. Per-file 64 MiB and total 512 MiB read limits; hit limits are marked.'
    files = $files.ToArray()
    strings = $hits.ToArray()
}
$output = Join-Path $OutputDirectory 'utility-static-report.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $output -Encoding UTF8
Write-Host "Files: $($files.Count); matching strings: $($hits.Count)"
Write-Host "Saved: $output"
Write-Host 'Attach utility-static-report.json to the chat. Review any private configuration strings before sharing.'
