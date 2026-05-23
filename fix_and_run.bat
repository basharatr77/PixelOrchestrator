@echo off
title Pixel Orchestrator - Environment Fix

echo =======================================
echo Creating a clean Python environment...
echo =======================================

REM Create a virtual environment
python -m venv venv

REM Activate it
call venv\Scripts\activate.bat

REM Upgrade pip and install PySide6 first (no cache to avoid corrupted wheels)
python -m pip install --upgrade pip
pip install --no-cache-dir PySide6

REM Install the rest of the requirements (skip any conflicting packages)
pip install -r requirements.txt

echo =======================================
echo Launching Pixel Orchestrator...
echo =======================================
python main_launcher.py

pause