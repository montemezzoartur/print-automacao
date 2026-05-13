@echo off
echo Detectando versao do Edge...
for /f "tokens=*" %%i in ('powershell -command "(Get-Item \"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe\").VersionInfo.ProductVersion"') do set EDGE_VERSION=%%i
echo Versao do Edge: %EDGE_VERSION%

echo Baixando Edge WebDriver...
powershell -command "Invoke-WebRequest -Uri 'https://msedgedriver.azureedge.net/%EDGE_VERSION%/edgedriver_win64.zip' -OutFile '%~dp0edgedriver.zip'"

echo Extraindo...
powershell -command "Expand-Archive -Path '%~dp0edgedriver.zip' -DestinationPath '%~dp0' -Force"

del "%~dp0edgedriver.zip"
echo.
echo Driver instalado com sucesso em: %~dp0msedgedriver.exe
pause
