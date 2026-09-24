@echo off
setlocal EnableExtensions EnableDelayedExpansion
title ASLAN TUNER - Release Builder
cd /d "%~dp0"

set "ROOT=%~dp0"
set "PYTHON=python"
if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"

echo.
echo ==================================================
echo           ASLAN TUNER RELEASE BUILDER
echo ==================================================
echo.

if not exist "%ROOT%version.txt" (
    echo [ERROR] version.txt not found.
    pause
    exit /b 1
)

set /p VERSION=<"%ROOT%version.txt"
if "%VERSION%"=="" (
    echo [ERROR] version.txt is empty.
    pause
    exit /b 1
)
echo [INFO] Version: %VERSION%
echo [INFO] Python: %PYTHON%
echo.

"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python 3.10+ and enable "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/6] Installing/checking build dependencies...
"%PYTHON%" -m pip install -r "%ROOT%requirements.txt"
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [2/6] Cleaning old build...
if exist "%ROOT%build" rmdir /s /q "%ROOT%build"
if exist "%ROOT%dist" rmdir /s /q "%ROOT%dist"
if exist "%ROOT%installer\Output" rmdir /s /q "%ROOT%installer\Output"
if exist "%ROOT%installer\install.generated.iss" del /q "%ROOT%installer\install.generated.iss"

echo.
echo [3/6] Building EXE with PyInstaller...
"%PYTHON%" -m PyInstaller --clean --noconfirm "%ROOT%ASLAN-TUNER.spec"
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

set "EXE=%ROOT%dist\ASLAN-TUNER-v%VERSION%.exe"
if not exist "%EXE%" (
    echo [ERROR] Expected EXE was not created:
    echo %EXE%
    pause
    exit /b 1
)

echo.
echo [4/6] Checking Inno Setup 6...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" (
    where ISCC.exe >nul 2>&1
    if not errorlevel 1 set "ISCC=ISCC.exe"
)

if "%ISCC%"=="" (
    echo [WARNING] Inno Setup 6 was not found.
    echo EXE build succeeded.
    echo Install Inno Setup 6, then run RELEASE.bat again.
    echo.
    echo EXE: %EXE%
    pause
    exit /b 0
)

echo.
echo [5/6] Preparing versioned Installer script...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=Get-Content -Raw '%ROOT%installer\install.iss'; $s=$s.Replace('@VERSION@','%VERSION%'); Set-Content -Encoding UTF8 '%ROOT%installer\install.generated.iss' $s"
if errorlevel 1 (
    echo [ERROR] Could not generate Installer script.
    pause
    exit /b 1
)

echo.
echo [6/6] Building Installer...
"%ISCC%" "%ROOT%installer\install.generated.iss"
if errorlevel 1 (
    echo [ERROR] Inno Setup build failed.
    echo EXE was created successfully:
    echo %EXE%
    pause
    exit /b 1
)

set "SETUP=%ROOT%installer\Output\ASLAN-TUNER-v%VERSION%-Setup.exe"
if not exist "%SETUP%" (
    echo [ERROR] Installer was not created where expected:
    echo %SETUP%
    pause
    exit /b 1
)

echo.
echo ==================================================
echo              RELEASE COMPLETE
echo ==================================================
echo.
echo EXE:
echo %EXE%
echo.
echo INSTALLER:
echo %SETUP%
echo.
echo Version %VERSION% is ready.
echo.
pause
exit /b 0
