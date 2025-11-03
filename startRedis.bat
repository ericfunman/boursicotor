@echo off
REM ========================================
REM  Lanceur Redis pour Boursicotor
REM ========================================

echo.
echo ========================================
echo  Redis Server - Boursicotor
echo ========================================
echo.

REM ========================================
REM CONFIGURATION MANUELLE
REM Si Redis ne se trouve pas automatiquement,
REM decommentez et modifiez la ligne ci-dessous:
REM ========================================
set REDIS_PATH_MANUAL=C:\redis\redis-server.exe

REM Chercher Redis dans les emplacements communs
set REDIS_PATH=

REM 0. Verifier si chemin manuel defini
if defined REDIS_PATH_MANUAL (
    if exist "%REDIS_PATH_MANUAL%" (
        set REDIS_PATH=%REDIS_PATH_MANUAL%
        goto :found
    )
)

REM 1. Chercher dans le repertoire courant
if exist "redis-server.exe" (
    set REDIS_PATH=redis-server.exe
    goto :found
)

REM 2. Chercher dans le dossier Redis local
if exist "redis\redis-server.exe" (
    set REDIS_PATH=redis\redis-server.exe
    goto :found
)

REM 3. Chercher dans Program Files
if exist "C:\Program Files\Redis\redis-server.exe" (
    set REDIS_PATH=C:\Program Files\Redis\redis-server.exe
    goto :found
)

REM 4. Chercher dans Chocolatey
if exist "C:\ProgramData\chocolatey\lib\redis-64\tools\redis-server.exe" (
    set REDIS_PATH=C:\ProgramData\chocolatey\lib\redis-64\tools\redis-server.exe
    goto :found
)

REM 5. Essayer directement (si dans PATH)
where redis-server.exe >nul 2>&1
if %errorlevel%==0 (
    set REDIS_PATH=redis-server.exe
    goto :found
)

REM Redis non trouve
echo [ERREUR] Redis n'a pas ete trouve !
echo.
echo Veuillez installer Redis:
echo.
echo Option 1 - Chocolatey (recommande):
echo   choco install redis-64
echo.
echo Option 2 - Manuel:
echo   1. Telecharger: https://github.com/microsoftarchive/redis/releases
echo   2. Extraire dans un dossier
echo   3. Copier le chemin et modifier ce script
echo.
pause
exit /b 1

:found
echo [OK] Redis trouve: %REDIS_PATH%
echo.
echo Demarrage de Redis...
echo.
echo ========================================
echo  Redis Server - EN COURS
echo  NE FERMEZ PAS CETTE FENETRE !
echo ========================================
echo.

"%REDIS_PATH%"

REM Si Redis s'arrete
echo.
echo ========================================
echo  Redis arrete
echo ========================================
pause
