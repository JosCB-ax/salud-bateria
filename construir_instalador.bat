@echo off
rem Crea el instalador de Salud de la bateria (instalador\SaludBateria-Setup-1.0.0.exe).
rem Basta con hacer doble clic. Solo hace falta tener Python instalado.
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo [1/4] Instalando las herramientas de empaquetado...
py -m pip install --upgrade pyinstaller -r requirements.txt
if errorlevel 1 goto error

echo.
echo [2/4] Creando SaludBateria.exe...
py -m PyInstaller --noconfirm --clean --windowed --name SaludBateria ^
  --icon icono.ico --add-data "icono.ico;." --version-file version.txt --hidden-import pystray._win32 app.py
if errorlevel 1 goto error

echo.
echo [3/4] Buscando Inno Setup (el programa que crea el instalador)...
call :buscar_iscc
if not defined ISCC (
  echo No esta instalado. Instalandolo con winget...
  winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements
  call :buscar_iscc
)
if not defined ISCC (
  echo.
  echo No se encuentra Inno Setup. Instalalo desde https://jrsoftware.org/isdl.php
  echo y vuelve a ejecutar este archivo.
  goto error
)

echo.
echo [4/4] Creando el instalador...
"%ISCC%" /Qp instalador.iss
if errorlevel 1 goto error

echo.
echo ============================================================
echo  Listo: instalador\SaludBateria-Setup-1.0.0.exe
echo  Copia ese archivo a cada portatil y ejecutalo para instalar.
echo ============================================================
explorer instalador
pause
exit /b 0

:buscar_iscc
set "ISCC="
for %%D in ("%ProgramFiles(x86)%" "%ProgramFiles%" "%LocalAppData%\Programs") do (
  if exist "%%~D\Inno Setup 6\ISCC.exe" set "ISCC=%%~D\Inno Setup 6\ISCC.exe"
)
exit /b 0

:error
echo.
echo Algo ha fallado. Copia lo que aparece arriba y pegalo en el chat.
pause
exit /b 1
