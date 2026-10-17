@echo off
setlocal
cd /d "%~dp0"

where git.exe >nul 2>&1
if errorlevel 1 (
    echo Git for Windows was not found in PATH.
    exit /b 1
)

set "SWITCHLENS_PLINK="
for /f "delims=" %%P in ('where plink.exe 2^>nul') do if not defined SWITCHLENS_PLINK set "SWITCHLENS_PLINK=%%P"
if not defined SWITCHLENS_PLINK if exist "%ProgramFiles%\PuTTY\plink.exe" set "SWITCHLENS_PLINK=%ProgramFiles%\PuTTY\plink.exe"
if not defined SWITCHLENS_PLINK if exist "%ProgramFiles(x86)%\PuTTY\plink.exe" set "SWITCHLENS_PLINK=%ProgramFiles(x86)%\PuTTY\plink.exe"
if not defined SWITCHLENS_PLINK (
    echo plink.exe was not found. Add your PuTTY directory to PATH and retry.
    exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo The .git directory is missing. Extract the complete repository archive.
    exit /b 1
)

if not "%~1"=="" set "SWITCHLENS_SSH_KEY=%~1"
if not defined SWITCHLENS_SSH_KEY set "SWITCHLENS_SSH_KEY=%USERPROFILE%\.ssh\adsdev.ppk"
if not exist "%SWITCHLENS_SSH_KEY%" (
    echo Private key file was not found: "%SWITCHLENS_SSH_KEY%"
    echo Usage: push-windows.cmd "C:\path\to\key.ppk"
    exit /b 1
)

set GIT_SSH_COMMAND="%SWITCHLENS_PLINK%" -ssh -l git -noagent -noshare -i "%SWITCHLENS_SSH_KEY%"
set "GIT_SSH_VARIANT=plink"

git remote set-url origin git@github.com:adsdevdoo/switchlens-sg1218.git
if errorlevel 1 exit /b 1

echo Using explicit key "%SWITCHLENS_SSH_KEY%" as SSH user git
echo Pageant and shared SSH connections are disabled for this push.
echo Pushing main and annotated version tags to git@github.com:adsdevdoo/switchlens-sg1218.git
git push --set-upstream --follow-tags origin main
if errorlevel 1 exit /b 1
echo Push completed.
exit /b 0
