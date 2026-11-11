@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" studio.py daily >> data\daily.log 2>&1
".venv\Scripts\python.exe" studio.py learn >> data\daily.log 2>&1
