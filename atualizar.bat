@echo off
setlocal
rem ============================================================================
rem  ATUALIZAR / INSTALAR  -  Gerador de Prompt
rem  Baixa a versao mais nova do GitHub e atualiza tudo de uma vez.
rem  NAO apaga o que e seu: dados\usuario.json, presets, historico e saidas.
rem  Pode ficar dentro da pasta do programa (atualiza ali) ou em qualquer outro
rem  lugar (instala na subpasta "gerador-de-prompt").
rem ============================================================================
set "REPO=teste0102/gerador-de-prompt"
set "BRANCH=claude/prompt-generator-gui-ir1a57"
set "ZIPURL=https://github.com/%REPO%/archive/refs/heads/%BRANCH%.zip"

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"
if exist "%HERE%\gerador_de_prompt.py" (
  set "DEST=%HERE%"
) else (
  set "DEST=%HERE%\gerador-de-prompt"
)

set "WORK=%TEMP%\gdp_update"
if exist "%WORK%" rd /s /q "%WORK%"
mkdir "%WORK%"

echo.
echo  Baixando a versao mais nova do GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri '%ZIPURL%' -OutFile '%WORK%\gdp.zip'; Expand-Archive -Force -Path '%WORK%\gdp.zip' -DestinationPath '%WORK%\x'"
if errorlevel 1 goto erro_download

set "SRC="
for /d %%D in ("%WORK%\x\*") do set "SRC=%%D"
if not defined SRC goto erro_download
if not exist "%SRC%\gerador_de_prompt.py" goto erro_download

if not exist "%DEST%" mkdir "%DEST%"
echo  Atualizando arquivos em: %DEST%
robocopy "%SRC%" "%DEST%" /E /XD presets historico saidas /XF usuario.json atualizar.bat /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto erro_copia

echo.
echo  Pronto! Atualizado com sucesso.
echo  (seus presets, historico, saidas e palavras do dicionario foram mantidos)
echo.
if exist "%DEST%\executar.bat" call "%DEST%\executar.bat"

rem o proprio atualizar.bat tambem e atualizado, mas por ultimo e numa linha so
rem (o cmd nao pode ter o arquivo trocado no meio da execucao)
copy /y "%SRC%\atualizar.bat" "%HERE%\atualizar.bat" >nul 2>nul & rd /s /q "%WORK%" >nul 2>nul & exit /b 0

:erro_download
echo.
echo  ERRO: nao consegui baixar do GitHub.
echo  Confira a internet e tente de novo. Endereco:
echo  %ZIPURL%
echo.
pause
exit /b 1

:erro_copia
echo.
echo  ERRO: nao consegui copiar os arquivos para: %DEST%
echo  Feche o programa se ele estiver aberto e tente de novo.
echo.
pause
exit /b 1
