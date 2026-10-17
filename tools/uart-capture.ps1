#requires -Version 5.1
<# Receive-only capture. Connect adapter GND and RXD only. No serial writes. #>
[CmdletBinding()]
param(
    [ValidatePattern('^COM[0-9]+$')][string]$Port = 'COM3',
    [ValidateRange(300, 2000000)][int]$Baud = 38400,
    [ValidateRange(1, 3600)][int]$Seconds = 60,
    [string]$OutputDirectory = ''
)

$ErrorActionPreference = 'Stop'
$uart = $null
$raw = $null
$textLog = $null
$hexLog = $null
$timer = [Diagnostics.Stopwatch]::new()
$received = [long]0
$failure = $null
$completed = $false
$opened = $false
$exitCode = 0
$startedUtc = [DateTime]::UtcNow.ToString('o')
$sessionDirectory = $null

try {
    # Resolve the default after parameter binding, not in the param block.
    if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
        $scriptDirectory = $PSScriptRoot
        if ([string]::IsNullOrWhiteSpace($scriptDirectory) -and
            -not [string]::IsNullOrWhiteSpace($MyInvocation.MyCommand.Path)) {
            $scriptDirectory = [IO.Path]::GetDirectoryName($MyInvocation.MyCommand.Path)
        }
        if ([string]::IsNullOrWhiteSpace($scriptDirectory)) {
            $scriptDirectory = (Get-Location).ProviderPath
        }
        if ([string]::IsNullOrWhiteSpace($scriptDirectory)) {
            throw 'Cannot determine the log directory. Pass -OutputDirectory with a filesystem path.'
        }
        $OutputDirectory = Join-Path $scriptDirectory 'uart-logs'
    }
    $sessionName = '{0}-{1}-{2}-{3}' -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'), $Port, $Baud, ([Guid]::NewGuid().ToString('N').Substring(0, 8))
    $sessionDirectory = (New-Item -ItemType Directory -Path (Join-Path $OutputDirectory $sessionName) -Force).FullName
    $utf8 = [Text.UTF8Encoding]::new($false)
    $raw = [IO.File]::Open((Join-Path $sessionDirectory 'rx.bin'), [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    $textLog = [IO.StreamWriter]::new((Join-Path $sessionDirectory 'rx.txt'), $false, $utf8)
    $hexLog = [IO.StreamWriter]::new((Join-Path $sessionDirectory 'rx.hex.txt'), $false, $utf8)
    $textLog.AutoFlush = $true
    $hexLog.AutoFlush = $true

    $uart = [IO.Ports.SerialPort]::new($Port, $Baud, 'None', 8, 'One')
    $uart.Handshake = 'None'
    $uart.DtrEnable = $false
    $uart.RtsEnable = $false
    $uart.ReadTimeout = 200
    $uart.ReadBufferSize = 65536
    $uart.DiscardNull = $false
    $uart.ParityReplace = 0
    $uart.Open()
    $opened = $true
    $timer.Start()

    Write-Host "LISTENING: $Port, $Baud baud, 8N1, no flow control. RX ONLY."
    Write-Host "Power on the BENCH switch now. Recording for $Seconds seconds."
    Write-Host "Logs: $sessionDirectory"
    Write-Host 'No data is sent to the switch. Ctrl+C stops recording.'
    $buffer = [byte[]]::new(4096)
    while ($timer.Elapsed.TotalSeconds -lt $Seconds) {
        try {
            $count = $uart.Read($buffer, 0, $buffer.Length)
        } catch {
            if ($_.Exception.GetBaseException() -is [TimeoutException]) { continue }
            throw
        }
        if ($count -le 0) { continue }
        $raw.Write($buffer, 0, $count)
        $raw.Flush()
        $hex = [BitConverter]::ToString($buffer, 0, $count).Replace('-', ' ')
        $hexLog.WriteLine(('{0} offset=0x{1:X8} count={2} {3}' -f [DateTime]::UtcNow.ToString('o'), $received, $count, $hex))
        $received += $count
        $display = [Text.StringBuilder]::new()
        for ($i = 0; $i -lt $count; $i++) {
            $b = $buffer[$i]
            if (($b -ge 32 -and $b -le 126) -or $b -eq 9 -or $b -eq 10 -or $b -eq 13) {
                [void]$display.Append([char]$b)
            } else {
                [void]$display.Append(('\x{0:X2}' -f $b))
            }
        }
        $textLog.Write($display.ToString())
        Write-Host -NoNewline $display.ToString()
    }
    $completed = $true
} catch {
    $failure = $_.Exception.GetBaseException().Message
    $exitCode = 1
    Write-Host "`nERROR: $failure" -ForegroundColor Red
} finally {
    $timer.Stop()
    if ($null -ne $uart) { $uart.Dispose() }
    foreach ($stream in @($raw, $textLog, $hexLog)) {
        if ($null -ne $stream) { $stream.Dispose() }
    }
    if ($null -ne $sessionDirectory) {
        $metadata = [ordered]@{
            mode = 'receive-only'; port = $Port; baud = $Baud; framing = '8N1'
            started_utc = $startedUtc; elapsed_seconds = $timer.Elapsed.TotalSeconds
            requested_seconds = $Seconds; port_opened = $opened
            capture_completed = $completed; bytes_received = $received; error = $failure
            note = 'Zero bytes only describe this capture. Bench RX settings: switch J2 pin 1 TX, 38400 8N1; see docs/LAB.md for numbering and limits.'
        }
        $metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $sessionDirectory 'session.json') -Encoding UTF8
        Write-Host "`nReceived: $received bytes. Logs: $sessionDirectory"
        if ($opened -and $completed -and $received -eq 0) {
            Write-Host 'NO DATA: no bytes received during this capture.' -ForegroundColor Yellow
        }
    }
}
exit $exitCode
