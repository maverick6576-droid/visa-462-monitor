@echo off
REM ============================================================================
REM SCRIPT BATCH PARA EJECUCIÓN POR PROGRAMADOR DE TAREAS DE WINDOWS
REM ============================================================================
REM Cambia al directorio donde se encuentra este archivo .bat
cd /d "%~dp0"

REM Ejecuta una comprobación puntual de la Visa 462 y registra salida en monitor.log
python main.py --check >> monitor.log 2>&1
