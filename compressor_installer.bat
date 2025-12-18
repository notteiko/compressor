@echo off

set PYTHON_URL=https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe
set PYTHON_EXE=%TEMP%\python.exe
set SCRIPT_URL=https://raw.githubusercontent.com/notteiko/compressor/refs/heads/main/compressor3.py
set SCRIPT_FILE=%LOCALAPPDATA%\Compressor\compressor.py
mkdir %LOCALAPPDATA%\Compressor
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    goto :RUN_SCRIPT
)
echo Nemas nainstalovany python, na koniec budes musiet restartovat pc
echo Stahujem Python...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_EXE%'"

echo Instalujem Python...
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
powershell -Command "Invoke-WebRequest -Uri '%SCRIPT_URL%' -OutFile '%SCRIPT_FILE%'"

python "%SCRIPT_FILE%"
