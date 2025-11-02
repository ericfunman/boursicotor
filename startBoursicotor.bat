@echo off
REM ========================================
REM  Boursicotor - Launcher Script
REM  Double-cliquez pour lancer l'application
REM ========================================

echo.
echo ========================================
echo  Boursicotor - Trading Platform
echo ========================================
echo.

REM Aller dans le repertoire du script
cd /d "%~dp0"

REM Verifier si l'environnement virtuel existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERREUR] Environnement virtuel non trouve !
    echo.
    echo Veuillez d'abord executer setup.bat pour installer les dependances.
    echo.
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
echo [1/4] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Verifier si le fichier .env existe
if not exist ".env" (
    echo.
    echo [ATTENTION] Fichier .env non trouve !
    echo.
    echo Veuillez configurer vos credentials IBKR dans .env
    echo Vous pouvez copier .env.example vers .env et le modifier.
    echo.
    pause
)

echo [2/4] Configuration detectee

REM Empecher la mise en veille pendant l'execution
echo [INFO] Desactivation temporaire de la mise en veille...
powercfg /change standby-timeout-ac 0 2>NUL
powercfg /change standby-timeout-dc 0 2>NUL
powercfg /change monitor-timeout-ac 0 2>NUL
powercfg /change monitor-timeout-dc 0 2>NUL
echo [OK] Mise en veille desactivee

REM Definir le chemin vers IB Gateway
set IBGATEWAY_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Verifier si IB Gateway est deja lance (processus Java)
echo [2.1/4] Verification d'IB Gateway...
tasklist /FI "IMAGENAME eq java.exe" 2>NUL | find /I /N "java.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] IB Gateway est deja en cours d'execution
    goto :skip_ibgateway
)

REM IB Gateway n'est pas lance - utiliser IBC pour auto-login
echo [INFO] Lancement d'IB Gateway avec IBC (auto-login)...

REM Lancer IBC
set "IBC_LAUNCHER=C:\IBC\start_gateway.bat"
call "%IBC_LAUNCHER%"
echo [INFO] IB Gateway lance avec IBC (connexion automatique)
echo [INFO] Attente de l'initialisation complete (15 secondes)...
timeout /t 15 /nobreak >nul

:skip_ibgateway

REM Definir le chemin vers Redis
set REDIS_PATH=C:\redis\redis-server.exe

REM Verifier si Redis est deja lance
echo [3/4] Verification de Redis...
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Redis est deja en cours d'execution
) else (
    echo [INFO] Lancement de Redis...
    if exist "%REDIS_PATH%" (
        start "Redis Server - Boursicotor" "%REDIS_PATH%"
        echo [INFO] Attente du demarrage de Redis...
        timeout /t 3 /nobreak >NUL
        echo [OK] Redis demarre dans une fenetre separee
    ) else (
        echo.
        echo ========================================
        echo  [ERREUR] Redis non trouve !
        echo ========================================
        echo.
        echo Redis n'a pas ete trouve a: %REDIS_PATH%
        echo.
        echo Veuillez verifier l'installation de Redis
        echo ou modifier le chemin dans ce script.
        echo.
        pause
        exit /b 1
    )
)

REM Verifier si Celery est deja lance
echo [4/4] Verification de Celery Worker...
tasklist /FI "WINDOWTITLE eq Celery Worker*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Celery Worker est deja en cours d'execution
) else (
    REM Purger Redis ET Celery APRES que Redis soit lance
    echo [INFO] Nettoyage de Redis et de la queue Celery...
    
    REM Flush Redis to remove all persisted Celery data
    C:\redis\redis-cli.exe FLUSHALL > nul 2>&1
    
    REM Execute purge in a subshell to ensure venv is active
    cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && celery -A backend.celery_config purge -f" > nul 2>&1
    
    REM Clean up any stuck jobs in database
    cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && python cleanup_jobs.py" > nul 2>&1
    
    REM Note: purge returns exit code 0 even if queue was empty, so we just confirm it ran
    echo [OK] Redis et queue Celery nettoyes (demarrage propre)
    
    REM Petit delai pour s'assurer que le nettoyage est complete
    timeout /t 1 /nobreak >NUL
    
    echo [INFO] Lancement de Celery Worker...
    start "Celery Worker - Boursicotor" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && celery -A backend.celery_config worker --loglevel=info --pool=solo"
    timeout /t 3 /nobreak >NUL
    echo [OK] Celery Worker demarre
)

REM Lancer Streamlit
echo.
echo ========================================
echo  Application demarree !
echo  URL: http://localhost:8501
echo ========================================
echo.
echo IMPORTANT:
echo - Redis Server: Terminal separe ^(NE PAS FERMER^)
echo - Celery Worker: Terminal separe ^(NE PAS FERMER^)
echo - Streamlit: Cette fenetre
echo.
echo Appuyez sur Ctrl+C pour arreter Streamlit uniquement
echo.

"%~dp0venv\Scripts\streamlit.exe" run "%~dp0frontend\app.py"

REM Si Streamlit s'arrete
echo.
echo ========================================
echo  Streamlit arrete
echo ========================================
echo.
echo ATTENTION: Redis et Celery sont toujours en cours d'execution
echo Fermez manuellement les fenetres Redis et Celery si necessaire
echo.
pause
