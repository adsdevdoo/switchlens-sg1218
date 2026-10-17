@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0uart-capture.ps1" %*
set "SWITCHLENS_UART_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %SWITCHLENS_UART_EXIT%
