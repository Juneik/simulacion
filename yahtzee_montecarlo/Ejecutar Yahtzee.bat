@echo off
setlocal EnableDelayedExpansion
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

set modo=con

:menu
echo.
echo ============================================
echo   Yahtzee con Montecarlo
if "!modo!"=="con" (
    echo   Modo: con semilla. Los resultados se repiten.
) else (
    echo   Modo: sin semilla. Cada corrida sale distinta.
)
echo ============================================
echo   1  1 partida
echo   2  100 partidas
echo   3  10000 partidas
echo   4  100000 partidas
if "!modo!"=="con" (
    echo   5  Cambiar a modo sin semilla para resultados aleatorios
) else (
    echo   5  Cambiar a modo con semilla para resultados fijos
)
echo   6  Salir
echo.
set /p opcion=Escribe un numero y pulsa Enter: 

if "!opcion!"=="1" goto demo
if "!opcion!"=="2" goto cien
if "!opcion!"=="3" goto diezmil
if "!opcion!"=="4" goto cienmil
if "!opcion!"=="5" goto cambiar
if "!opcion!"=="6" goto fin

echo Opcion no valida.
goto menu

:cambiar
if "!modo!"=="con" (
    set modo=sin
) else (
    set modo=con
)
goto menu

:demo
call :preparar 1
echo.
echo Jugando una partida. Semilla: !semilla!
echo.
.venv\Scripts\python.exe main.py --demo --estrategia-1 avida --estrategia-2 seccion_superior --semilla !semilla!
echo.
pause
goto menu

:cien
call :preparar 100
echo.
echo Simulando 100 partidas. Semilla: !semilla!
echo Tarda unos segundos.
echo Las graficas quedan en !carpeta!
echo.
.venv\Scripts\python.exe main.py --suite --partidas 100 --semilla !semilla! --progreso 50 --salida !carpeta!
echo.
pause
goto menu

:diezmil
call :preparar 10000
echo.
echo Simulando 10000 partidas. Semilla: !semilla!
echo Tarda cerca de un minuto. No cierres la ventana.
echo Las graficas quedan en !carpeta!
echo.
.venv\Scripts\python.exe main.py --suite --partidas 10000 --semilla !semilla! --progreso 2500 --salida !carpeta!
echo.
pause
goto menu

:cienmil
call :preparar 100000
echo.
echo Simulando 100000 partidas. Semilla: !semilla!
echo Tarda varios minutos. No cierres la ventana.
echo Las graficas quedan en !carpeta!
echo.
.venv\Scripts\python.exe main.py --suite --partidas 100000 --semilla !semilla! --progreso 20000 --salida !carpeta!
echo.
pause
goto menu

:preparar
set npartidas=%~1
if "!modo!"=="con" (
    set semilla=42
    set carpeta=results\!npartidas!_partidas
) else (
    set /a semilla=!RANDOM! * 1000 + !RANDOM!
    set carpeta=results\sin_semilla\!npartidas!_partidas
)
exit /b 0

:fin
endlocal
exit /b 0
