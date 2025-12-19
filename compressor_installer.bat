@echo off

set REPO_ZIP=https://github.com/notteiko/compressor/archive/refs/heads/main.zip
set SCRIPT_DIR=%LOCALAPPDATA%\Compressor\compressor.zip
set ZIP_DIR=%LOCALAPPDATA%\%SCRIPT_DIR%
set PYTHON_URL=https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe
set PYTHON_EXE=%TEMP%\python.exe
mkdir %LOCALAPPDATA%\Compressor

python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    goto :RUN_SCRIPT
)

echo Nemas nainstalovany python, na koniec budes musiet restartovat pc
echo Stahujem Python...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_EXE%'"

echo Instalujem Python, potvrd UAC...
"%PYTHON_EXE%" /quiet InstallAllUsers=1 PrependPath=1

set PATH=%PATH%;C:\Program Files\Python312\;C:\Program Files\Python312\Scripts\
echo Python nainstalovany, restartovat teraz?
choice /M "Restartovat teraz?"
if %ERRORLEVEL% EQU 1 (
    shutdown /r /t 0
) else (
    exit
)

:RUN_SCRIPT
:: Download the Python script
powershell -Command "Invoke-WebRequest -Uri '%REPO_ZIP%' -OutFile '%SCRIPT_DIR%'"
powershell -Command "Expand-Archive '%SCRIPT_DIR%' -Force -DestinationPath '%LOCALAPPDATA%'"

python "%SCRIPT_DIR%"
