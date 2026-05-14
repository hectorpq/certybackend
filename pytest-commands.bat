@echo off
REM Script para ejecutar comandos de pytest en Windows
REM Uso: pytest-commands.bat <comando>

setlocal enabledelayedexpansion

if "%1"=="" goto usage
if "%1"=="help" goto usage
if "%1"=="?" goto usage

REM Colores (simulados)
set GREEN=[32m
set BLUE=[34m
set YELLOW=[33m
set RED=[31m
set RESET=[0m

goto %1

:all
echo.
echo %BLUE%Ejecutando todas las pruebas...%RESET%
call python -m pytest -v
goto end

:integration
echo.
echo %BLUE%Ejecutando pruebas de INTEGRACION...%RESET%
call python -m pytest -m integration -v
goto end

:unit
echo.
echo %BLUE%Ejecutando pruebas UNITARIAS...%RESET%
call python -m pytest -m unit -v
goto end

:events
echo.
echo %BLUE%Ejecutando pruebas de la app 'events'...%RESET%
call python -m pytest events/ -v
goto end

:coverage
echo.
echo %BLUE%Ejecutando pruebas con cobertura (terminal)...%RESET%
call python -m pytest --cov=. --cov-report=term-missing --cov-report=xml:coverage.xml
echo.
echo %GREEN%Reporte XML generado: coverage.xml%RESET%
goto end

:coverage-html
echo.
echo %BLUE%Generando reporte HTML de cobertura...%RESET%
call python -m pytest --cov=. --cov-report=html:htmlcov --cov-report=term-missing
echo.
echo %GREEN%Reporte HTML generado: htmlcov/index.html%RESET%
echo Abre el archivo en tu navegador para ver el reporte
goto end

:coverage-sonar
echo.
echo %BLUE%Generando cobertura para SonarQube...%RESET%
call python -m pytest --cov=. --cov-report=xml:coverage.xml -v
echo.
echo %GREEN%Archivo listo para SonarQube: coverage.xml%RESET%
goto end

:verbose
echo.
echo %BLUE%Ejecutando pruebas en modo VERBOSE...%RESET%
call python -m pytest -vv --tb=long -s
goto end

:last-failed
echo.
echo %BLUE%Ejecutando solo pruebas que fallaron...%RESET%
call python -m pytest --lf -v
goto end

:pdb
echo.
echo %BLUE%Ejecutando con debugger (pdb) activado...%RESET%
call python -m pytest --pdb -x
goto end

:collect
echo.
echo %BLUE%Listando todos los tests disponibles...%RESET%
call python -m pytest --collect-only -q
goto end

:usage
cls
echo.
echo =====================================================================
echo       PYTEST - Comandos Disponibles para CertyPro Backend
echo =====================================================================
echo.
echo Uso: pytest-commands.bat ^<comando^>
echo.
echo Comandos disponibles:
echo.
echo   all               - Ejecutar todas las pruebas
echo   integration       - Ejecutar solo pruebas de integracion
echo   unit              - Ejecutar solo pruebas unitarias
echo   events            - Ejecutar pruebas de la app 'events'
echo   coverage          - Ejecutar con reporte de cobertura
echo   coverage-html     - Generar reporte HTML de cobertura
echo   coverage-sonar    - Generar cobertura para SonarQube
echo   verbose           - Ejecutar con output detallado
echo   last-failed       - Ejecutar solo tests que fallaron
echo   pdb               - Ejecutar con debugger en caso de error
echo   collect           - Listar todos los tests disponibles
echo   help              - Mostrar esta ayuda
echo.
echo Ejemplos:
echo   pytest-commands.bat all
echo   pytest-commands.bat integration
echo   pytest-commands.bat coverage
echo.
goto end

:end
echo.
echo Completado
exit /b 0
