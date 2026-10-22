@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo No se encontro Python dentro de esta carpeta.
    echo Pide ayuda para crear el entorno .venv antes de volver a abrir este archivo.
    echo.
    pause
    exit /b 1
)

:menu
echo.
echo ============================================
echo   Yahtzee con Montecarlo
echo ============================================
echo   1  Ver una partida, turno a turno
echo   2  Simular 10000 partidas y crear las graficas
echo   3  Salir
echo.
set /p opcion=Escribe 1, 2 o 3 y pulsa Enter: 

if "%opcion%"=="1" goto demo
if "%opcion%"=="2" goto suite
if "%opcion%"=="3" goto fin

echo Opcion no valida.
goto menu

:demo
echo.
echo Jugando una partida. Espera a que aparezca el texto.
echo.
.venv\Scripts\python.exe main.py --demo --estrategia-1 avida --estrategia-2 seccion_superior --semilla 42
echo.
pause
goto menu

:suite
echo.
echo Esto tarda cerca de un minuto. No cierres la ventana.
echo Las graficas quedan en la carpeta results
echo.
.venv\Scripts\python.exe main.py --suite --partidas 10000 --semilla 42
echo.
pause
goto menu

:fin
exit /b 0
