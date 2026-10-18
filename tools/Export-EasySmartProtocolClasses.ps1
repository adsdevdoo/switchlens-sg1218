# Export selected Java class bytes as JSON. Never executes the utility or classes.
param(
    [string]$ZipPath = (Join-Path $env:USERPROFILE 'Downloads\EasySmartConfigurationUtility.zip'),
    [string]$OutputDirectory = 'C:\tmp'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$null = New-Item -ItemType Directory -Path $OutputDirectory -Force
$expectedHash = 'aa6e67c6e9be38cca002b704bc2eb1bf2b8fc199631e307a781cc7680c8d8619'
$outer = [IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    $entry = @($outer.Entries | Where-Object { $_.Name -eq 'Easy Smart Configuration Utility.exe' })
    if ($entry.Count -ne 1) { throw 'Expected exactly one launcher EXE' }
    if ($entry[0].Length -ne 1164102) { throw 'Unexpected launcher length; no export performed' }
    $st = $entry[0].Open()
    $memory = New-Object IO.MemoryStream
    try { $st.CopyTo($memory); $exeBytes = $memory.ToArray() } finally { $st.Dispose(); $memory.Dispose() }
} finally { $outer.Dispose() }
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $exeHash = ([BitConverter]::ToString($sha.ComputeHash($exeBytes))).Replace('-','').ToLowerInvariant()
    if ($exeHash -ne $expectedHash) { throw "Launcher hash differs from inspected report: $exeHash" }
    # Offsets from the owner's successful embedded-ZIP report, pinned by the EXE hash.
    $baseOffset = 63488
    $zipLength = 1164102 - $baseOffset
    $jarBytes = New-Object byte[] $zipLength
    [Array]::Copy($exeBytes,$baseOffset,$jarBytes,0,$zipLength)
    $jarMemory = New-Object IO.MemoryStream
    $jarMemory.Write($jarBytes,0,$jarBytes.Length)
    $jarMemory.Position = 0
    $jar = [IO.Compression.ZipArchive]::new($jarMemory,[IO.Compression.ZipArchiveMode]::Read,$false)
    $exportedClasses = New-Object 'System.Collections.Generic.List[object]'
    $totalBytes = 0
    $selection = '^com/tplink/smb/easySmartUtility/(?:[^/]+\.class|transfer/.+\.class|util/.+\.class|pages/switchdiscovery/bean/RSAKeyBean\.class|pages/switchdiscovery/controller/SwitchLoginController\.class)$'
    try {
        foreach ($e in $jar.Entries) {
            if (![regex]::IsMatch($e.FullName,$selection)) { continue }
            if ($e.Length -gt 1048576 -or ($totalBytes + $e.Length) -gt 4194304) { throw 'Class export size limit exceeded' }
            $cs = $e.Open()
            $cm = New-Object IO.MemoryStream
            try { $cs.CopyTo($cm); $classBytes = $cm.ToArray() } finally { $cs.Dispose();$cm.Dispose() }
            if ($classBytes.Length -lt 4 -or
                $classBytes[0] -ne 202 -or $classBytes[1] -ne 254 -or
                $classBytes[2] -ne 186 -or $classBytes[3] -ne 190) { throw "Invalid class header: $($e.FullName)" }
            $classHash = ([BitConverter]::ToString($sha.ComputeHash($classBytes))).Replace('-','').ToLowerInvariant()
            $exportedClasses.Add([pscustomobject]@{
                path = $e.FullName
                bytes = $classBytes.Length
                sha256 = $classHash
                base64 = [Convert]::ToBase64String($classBytes)
            })
            $totalBytes += $classBytes.Length
        }
    } finally { $jar.Dispose();$jarMemory.Dispose() }
} finally { $sha.Dispose() }
if (!$exportedClasses.Count) { throw 'No selected classes found' }
$output = Join-Path $OutputDirectory ('easysmart-protocol-classes-' + [guid]::NewGuid().ToString('N') + '.json')
$report = [ordered]@{
    format = 'SwitchLens Easy Smart Java class export v1'
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    exe_sha256 = $exeHash
    source_archive = [IO.Path]::GetFileName($ZipPath)
    application_executed = $false
    device_contacted = $false
    selection_regex = $selection
    class_count = $exportedClasses.Count
    total_class_bytes = $totalBytes
    classes = $exportedClasses.ToArray()
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $output -Encoding UTF8
Write-Host "Exported $($exportedClasses.Count) classes; $totalBytes bytes."
Write-Host "Saved: $output"
Write-Host 'Upload this JSON into the repository research directory, then send its branch/file link.'
