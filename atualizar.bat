@echo off
rem Atualiza o Gerador de Prompt com o Git (git pull). Nao baixa nada por PowerShell.
rem Seus dados (dados\usuario.json, presets, historico, saidas) nao sao tocados.
cd /d "%~dp0"

where git >nul 2>nul
if errorlevel 1 (
  echo.
  echo  Git nao encontrado. Instale uma vez, no PowerShell:
  echo      winget install -e --id Git.Git
  echo  depois feche e abra o PowerShell e rode este arquivo de novo.
  echo.
  pause
  exit /b 1
)

if not exist ".git" (
  echo.
  echo  Esta pasta nao foi baixada com o Git, entao nao da para atualizar aqui.
  echo  Baixe uma vez com:
  echo      git clone -b claude/prompt-generator-gui-ir1a57 https://github.com/teste0102/gerador-de-prompt gerador-de-prompt-git
  echo  e use o atualizar.bat da pasta nova.
  echo.
  pause
  exit /b 1
)

echo.
echo  Atualizando do GitHub...
git pull --ff-only origin claude/prompt-generator-gui-ir1a57
if errorlevel 1 (
  echo.
  echo  ERRO ao atualizar. Se voce mudou algum arquivo do programa a mao, desfaca com:
  echo      git checkout -- .
  echo  e rode de novo.
  echo.
  pause
  exit /b 1
)

echo.
echo  Pronto! Atualizado.
echo.
if exist "executar.bat" call "executar.bat"
