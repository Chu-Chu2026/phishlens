@echo off
REM Thin wrapper — prefers the Python one-shot script.
cd /d "%~dp0\.."
python scripts\setup_and_run.py %*
