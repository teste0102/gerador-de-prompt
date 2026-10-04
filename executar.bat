@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py gerador_de_prompt.py) || (python gerador_de_prompt.py)
if errorlevel 1 pause
