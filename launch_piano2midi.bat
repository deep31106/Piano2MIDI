
@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Main Python environment not found.
    echo Please check the .venv folder.
    pause
    exit /b 1
)

if not exist ".venv-transkun311\Scripts\transkun.exe" (
    echo WARNING: Transkun executable not found.
    echo Check your Transkun environment.
    pause
)

".venv\Scripts\python.exe" -m piano2midi.gui

if errorlevel 1 (
    echo.
    echo Piano2MIDI exited with an error.
    pause
)
