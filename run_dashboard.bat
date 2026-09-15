@echo off
setlocal enabledelayedexpansion
title Dashboard de Ejecucion Presupuestaria DIPRES

REM 1. Posicionarse en la carpeta donde reside este script
cd /d "%~dp0"

echo ===============================================================
echo     INICIANDO DASHBOARD DE EJECUCION PRESUPUESTARIA DIPRES
echo ===============================================================
echo.

REM 2. Deteccion de Python portable integrado
if exist "%~dp0runtime\python.exe" (
    set "PY_CMD=%~dp0runtime\python.exe"
    echo [OK] Entorno portable detectado. No requiere instalar nada.
) else (
    set "PY_CMD=python"
    echo [AVISO] Entorno portable no encontrado. Usando Python del sistema...
)

echo [OK] Iniciando dashboard y servicios...
echo.

REM 3. Ejecutar el orquestador principal
"%PY_CMD%" run_online.py

REM 4. Si se produce un error, mantener la ventana abierta
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ===============================================================
    echo [!] El proceso se detuvo con codigo de salida: %ERRORLEVEL%
    echo ===============================================================
    pause
)
