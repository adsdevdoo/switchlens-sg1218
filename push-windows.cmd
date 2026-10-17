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

set GIT_SSH_COMMAND="%SWITCHLENS_PLINK%" -ssh -agent
set "GIT_SSH_VARIANT=plink"

git remote set-url origin git@github.com:adsdevdoo/switchlens-sg1218.git
if errorlevel 1 exit /b 1

echo Using Pageant via "%SWITCHLENS_PLINK%"
echo Pushing main to git@github.com:adsdevdoo/switchlens-sg1218.git
git push --set-upstream origin main
if errorlevel 1 exit /b 1
echo Push completed.
exit /b 0
