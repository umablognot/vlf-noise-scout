@echo off
setlocal EnableDelayedExpansion
title VLF Noise Scout - Server
cd /d "%~dp0server"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found on PATH. Install it from https://python.org
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment...
    python -m venv .venv || goto :err
)

".venv\Scripts\python.exe" -c "import sounddevice, uvicorn, fastapi, numpy, dotenv" >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Installing required packages...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :err
    ".venv\Scripts\python.exe" -c "import sounddevice, uvicorn, fastapi, numpy, dotenv" || goto :err
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [WARNING] ffmpeg not found on PATH. The MP3 stream will not work.
    echo           Install it with:  winget install Gyan.FFmpeg
    echo           Then close this window and start again.
    pause
)

echo.
echo ================= AUDIO DEVICES =================
".venv\Scripts\python.exe" -c "import sounddevice; print(sounddevice.query_devices())"
echo =================================================
echo.
echo Find the stereo Line-In device above (2 input channels).
set "VLF_DEVICE="
set /p VLF_DEVICE="Device number (Enter = use .env / system default): "

echo.
echo Starting server at http://localhost:8000  (Ctrl+C to stop)
echo.
".venv\Scripts\python.exe" -m uvicorn vlf_stream.server:app --host 0.0.0.0 --port 8000
pause
exit /b 0

:err
echo.
echo [ERROR] Setup failed. Check the messages above.
pause
exit /b 1
