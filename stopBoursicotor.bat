@echo off
REM ========================================
REM  Boursicotor - Stop Script
REM  Arrete tous les services (Redis, Celery, Streamlit)
REM ========================================

echo.
echo ========================================
echo  Boursicotor - Arret des services
echo ========================================
echo.

REM Arreter Streamlit
echo [1/3] Arret de Streamlit...
taskkill /F /IM streamlit.exe 2>NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Streamlit arrete
) else (
    echo [INFO] Streamlit n'etait pas en cours d'execution
)

REM Arreter Celery (processus Python avec celery worker)
echo [2/3] Arret de Celery Worker...
for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq Celery Worker*" /NH /FO CSV 2^>NUL ^| find "cmd.exe"') do (
    taskkill /F /PID %%~a 2>NUL
)
REM Aussi arreter les processus Python de Celery
wmic process where "commandline like '%%celery%%worker%%'" delete 2>NUL
echo [OK] Celery Worker arrete

REM Arreter Redis
echo [3/3] Arret de Redis...
taskkill /F /IM redis-server.exe 2>NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Redis arrete
) else (
    echo [INFO] Redis n'etait pas en cours d'execution
)

REM Restaurer les parametres de mise en veille (30 min sur secteur, 15 min sur batterie)
echo.
echo [INFO] Restauration des parametres de mise en veille...
powercfg /change standby-timeout-ac 30
powercfg /change standby-timeout-dc 15
powercfg /change monitor-timeout-ac 10
powercfg /change monitor-timeout-dc 5
echo [OK] Parametres de mise en veille restaures

echo.
echo ========================================
echo  Tous les services sont arretes
echo ========================================
echo.
pause
