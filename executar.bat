@echo off
rem Abre o Gerador de Prompt. Procura o Python sozinho (nao depende do PATH).
cd /d "%~dp0"
set "PY="
for %%P in (
  "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
  "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
  "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
  "%ProgramFiles%\Python313\pythonw.exe"
  "%ProgramFiles%\Python312\pythonw.exe"
  "%ProgramFiles%\Python311\pythonw.exe"
) do if not defined PY if exist %%P set "PY=%%~P"
if defined PY (
  start "" "%PY%" gerador_de_prompt.py
  exit /b
)
where pythonw >nul 2>nul && (start "" pythonw gerador_de_prompt.py & exit /b)
where py >nul 2>nul && (start "" py -3 gerador_de_prompt.py & exit /b)
echo.
echo Python nao encontrado. Instale em https://www.python.org/downloads/windows/
echo (marque "Add python.exe to PATH") ou rode:  winget install -e --id Python.Python.3.12
echo.
pause
