@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo  No encuentro Python en este ordenador.
    echo  Instalalo desde https://www.python.org/downloads/
    echo  y al instalar MARCA la casilla "Add python.exe to PATH".
    echo  Despues vuelve a hacer doble clic en INICIAR.bat
    echo.
    pause
    exit /b
)
python Scripts\menu.py
echo.
pause
