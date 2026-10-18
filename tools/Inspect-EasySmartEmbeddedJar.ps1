# Inspect an embedded ZIP/JAR in the Easy Smart launcher without executing it.
param(
    [string]$ZipPath = (Join-Path $env:USERPROFILE 'Downloads\EasySmartConfigurationUtility.zip'),
    [string]$OutputDirectory = 'C:\tmp'
)
$ErrorActionPreference = 'Stop'
$null = New-Item -ItemType Directory -Path $OutputDirectory -Force
Add-Type -AssemblyName System.IO.Compression.FileSystem
$outer = [IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    $entry = @($outer.Entries | Where-Object { $_.Name -eq 'Easy Smart Configuration Utility.exe' })
    if ($entry.Count -ne 1) { throw 'Expected exactly one Easy Smart Configuration Utility.exe' }
    $stream = $entry[0].Open()
    $ms = New-Object IO.MemoryStream
    try { $stream.CopyTo($ms); $data = $ms.ToArray() } finally { $stream.Dispose(); $ms.Dispose() }
} finally { $outer.Dispose() }
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($data))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
$found = $null
# Classic single-disk ZIP only. Validate central directory and first local header.
for ($i = $data.Length - 22; $i -ge 0; $i--) {
    if ($data[$i] -ne 80 -or $data[$i+1] -ne 75 -or $data[$i+2] -ne 5 -or $data[$i+3] -ne 6) { continue }
    $end = [long]$i + 22 + [BitConverter]::ToUInt16($data,$i+20)
    $size = [long][BitConverter]::ToUInt32($data,$i+12)
    $off = [long][BitConverter]::ToUInt32($data,$i+16)
    $base = [long]$i - $size - $off
    $cd = [long]$i - $size
    if ($end -gt $data.Length -or $base -lt 0 -or $cd -lt $base -or $cd -gt ($i-46)) { continue }
    if ([BitConverter]::ToUInt16($data,$i+4) -ne 0 -or [BitConverter]::ToUInt16($data,$i+6) -ne 0) { continue }
    if ($data[$cd] -ne 80 -or $data[$cd+1] -ne 75 -or $data[$cd+2] -ne 1 -or $data[$cd+3] -ne 2) { continue }
    $local = $base + [long][BitConverter]::ToUInt32($data,[int]$cd+42)
    if ($local -lt 0 -or $local -gt ($cd-4)) { continue }
    if ($data[$local] -ne 80 -or $data[$local+1] -ne 75 -or $data[$local+2] -ne 3 -or $data[$local+3] -ne 4) { continue }
    $found = [ordered]@{ base_offset = $base; end_offset = $end; entry_count = [BitConverter]::ToUInt16($data,$i+10) }
    break
}
if ($null -eq $found) {
    [ordered]@{ exe_sha256=$hash; result='NO_VALID_CLASSIC_EMBEDDED_ZIP_FOUND'; note='Does not exclude resources, encryption or other packaging.' } | ConvertTo-Json
    return
}
$buffer = New-Object byte[] ([int]($found.end_offset-$found.base_offset))
[Array]::Copy($data,[int]$found.base_offset,$buffer,0,$buffer.Length)
$mem = New-Object IO.MemoryStream
$mem.Write($buffer,0,$buffer.Length)
$mem.Position = 0
$jar = [IO.Compression.ZipArchive]::new($mem,[IO.Compression.ZipArchiveMode]::Read,$false)
$rows = New-Object 'System.Collections.Generic.List[object]'
$protocolEntries = New-Object 'System.Collections.Generic.List[object]'
$manifest = $null
$total = [long]0
try {
    foreach ($e in $jar.Entries) {
        $rows.Add([pscustomobject]@{path=$e.FullName;bytes=$e.Length})
        if ($e.Length -gt 4194304 -or ($total+$e.Length) -gt 67108864) { continue }
        if ($e.FullName -notmatch '\.(class|properties|xml|txt|MF)$') { continue }
        $st = $e.Open(); $m = New-Object IO.MemoryStream
        try { $st.CopyTo($m); $bytes=$m.ToArray() } finally { $st.Dispose();$m.Dispose() }
        $total += $bytes.Length
        if ($e.FullName -eq 'META-INF/MANIFEST.MF') { $manifest=[Text.Encoding]::UTF8.GetString($bytes) }
        $raw = [Text.Encoding]::GetEncoding(28591).GetString($bytes)
        $terms = New-Object 'System.Collections.Generic.List[string]'
        foreach ($hit in [regex]::Matches($raw,'[\x20-\x7E]{4,}')) {
            if ($hit.Value -match '(?i)tddp|tsdp|datagram|packet|factory|flash|signature|sha.?1|md5|rsa|opcode|command|password|encrypt|decrypt|macaddress') {
                $terms.Add($hit.Value.Substring(0,[Math]::Min(240,$hit.Value.Length)))
            }
        }
        if ($terms.Count) { $protocolEntries.Add([pscustomobject]@{path=$e.FullName;terms=@($terms | Select-Object -Unique)}) }
    }
} finally { $jar.Dispose(); $mem.Dispose() }
$out = Join-Path $OutputDirectory ('easysmart-jar-' + [guid]::NewGuid().ToString('N') + '.json')
$report = [ordered]@{
    result='EMBEDDED_ZIP_PARSED'; exe_sha256=$hash; zip=$found; manifest=$manifest
    device_contacted=$false; application_executed=$false
    limitations='Printable class strings, not a bytecode disassembly; no recursive nested JAR analysis. 4 MiB per entry / 64 MiB scan budget.'
    entries=$rows.ToArray(); matching_entries=$protocolEntries.ToArray()
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding UTF8
$priority = @($protocolEntries | Where-Object { ($_.path + ' ' + ($_.terms -join ' ')) -match '(?i)tddp|tsdp|datagram|opcode' })
if (!$priority.Count) { $priority = @($protocolEntries | Select-Object -First 12) }
[ordered]@{
    result=$report.result; exe_sha256=$hash; zip=$found; manifest=$manifest
    total_entries=$rows.Count; matching_entries=$protocolEntries.Count
    class_sample=@($rows | Where-Object { $_.path -match '\.class$' } | Select-Object -First 20)
    priority=@($priority | Select-Object -First 12 | ForEach-Object {
        [pscustomobject]@{path=$_.path;terms=@($_.terms | Select-Object -First 16)}
    })
} | ConvertTo-Json -Depth 8
Write-Host "Full report: $out"
Write-Host 'Paste the summary above into GitHub issue #1.'
