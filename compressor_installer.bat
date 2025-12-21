@echo off

set REPO_ZIP=https://github.com/notteiko/compressor/archive/refs/heads/main.zip
set SCRIPT_DIR=%TEMP%\compressor.zip
set ZIP_DIR=%LOCALAPPDATA%\%SCRIPT_DIR%
set PYTHON_URL=https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe
set PYTHON_EXE=%TEMP%\python.exe

python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    goto :RUN_SCRIPT
)

echo Aby si toto mohol pouzivat, potrebujes ffmpeg, python a nepovinne cuda (to ti zrychli encoding videa milion krat ked mas nvidia grafiku)
echo.
echo.
echo.
echo.
echo Python nemas nainstalovany
echo Stahujem Python...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_EXE%'"

echo Instalujem Python, potvrd UAC...
"%PYTHON_EXE%" /quiet InstallAllUsers=1 PrependPath=1

echo Python nainstalovany, restartovat teraz? Po restartovani zapni tento instalator este raz
choice /C AN /N /M "Restartovat teraz? [A=ANO, N=NIE]: "
if %ERRORLEVEL% EQU 1 (
    shutdown /r /t 0
) else (
    exit
)

:RUN_SCRIPT
:: Download the Python script
powershell -Command "Invoke-WebRequest -Uri '%REPO_ZIP%' -OutFile '%SCRIPT_DIR%'"
powershell -Command "Expand-Archive '%SCRIPT_DIR%' -Force -DestinationPath '%LOCALAPPDATA%'"

python "%LOCALAPPDATA%\compressor-main\compressor3.py"
