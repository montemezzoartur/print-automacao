@echo off
setlocal enabledelayedexpansion
title Print Automacao — Instalador
cd /d "%~dp0"

echo.
echo  ============================================
echo    Print Automacao - Instalador
echo  ============================================
echo.

:: ---------- Localizar Python ----------
set PY=

for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%P (
        set PY=%%~P
        goto :python_ok
    )
)

python --version >nul 2>&1
if %errorlevel%==0 (
    set PY=python
    goto :python_ok
)

echo [!] Python nao encontrado. Baixando Python 3.12...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%TEMP%\python_installer.exe' -UseBasicParsing"
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao baixar o Python. Verifique a conexao com a internet.
    pause & exit /b 1
)
echo Instalando Python 3.12 (aguarde)...
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
del "%TEMP%\python_installer.exe" >nul 2>&1
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

:python_ok
echo [OK] Python: %PY%

:: ---------- Dependencias ----------
echo.
echo Instalando dependencias...
"%PY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
"%PY%" -m pip install -r "%~dp0requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias.
    pause & exit /b 1
)
echo [OK] Dependencias instaladas.

:: ---------- config.py ----------
echo.
if not exist "%~dp0config.py" (
    copy "%~dp0config.exemplo.py" "%~dp0config.py" >nul
    echo [OK] config.py criado. Abrindo para voce preencher usuario e senha...
    timeout /t 2 >nul
    notepad "%~dp0config.py"
) else (
    echo [OK] config.py ja existe.
)

:: ---------- Salvar caminho do Python no iniciar.bat ----------
echo @echo off > "%~dp0iniciar.bat"
echo cd /d "%%~dp0" >> "%~dp0iniciar.bat"
echo "%PY%" "%%~dp0main.py" >> "%~dp0iniciar.bat"

:: ---------- Atalho na area de trabalho ----------
echo.
powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell;" ^
    "$s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Print Automacao.lnk');" ^
    "$s.TargetPath = '%~dp0iniciar.bat';" ^
    "$s.WorkingDirectory = '%~dp0';" ^
    "$s.WindowStyle = 1;" ^
    "$s.Save()"
echo [OK] Atalho criado na area de trabalho.

echo.
echo  ============================================
echo    Instalacao concluida!
echo  ============================================
echo.
echo  Proximos passos:
echo   1. Certifique-se de que o config.py esta
echo      preenchido com usuario e senha do PACS
echo   2. Use o atalho "Print Automacao" na area
echo      de trabalho para iniciar o app
echo.
pause
