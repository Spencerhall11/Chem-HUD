@echo off
title ChemHUD Master Launcher
color 0B

@echo off
:: Force Admin Elevation
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrative Privileges...
    powershell start-process -FilePath '%0' -verb runas
    exit /b
)

title ChemHUD Master Launcher
color 0B
cd /d "E:\ChemHUD"

echo --- Initializing ChemHUD System ---
start "" "ScreenReaderEye.exe"
timeout /t 2 >nul

echo [3/3] Connecting Nerve to Brain...
:: Using 'call' ensures the pipe stays alive in the new window
start cmd /k "python Nerve.py | cabal run -v0"

echo --- Full Stack Active ---
pause




echo --- Initializing ChemHUD System ---

:: 1. Start the C++ Eye (The Producer)
echo [1/3] Launching ScreenReaderEye...
start "" "E:\ChemHUD\ScreenReaderEye.exe"

:: 2. Wait for the Shared Memory Buffer to initialize
echo [2/3] Waiting for Shared Memory Buffer...
timeout /t 2 >nul

:: 3. Launch the Nerve and Brain Pipe
echo [3/3] Connecting Nerve to Brain...
:: This starts a new window for the Python/Haskell interaction
start cmd /k "cd /d E:\ChemHUD && python Nerve.py | cabal run -v0"

echo --- Full Stack Active ---
echo Close the Eye and the Nerve windows to shut down.
pause