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
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change monitor-timeout-ac 0
powercfg /change monitor-timeout-dc 0
echo [OK] Mise en veille desactivee (sera restauree a l'arret)

REM Definir le chemin vers IB Gateway
set IBGATEWAY_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

REM Verifier si IB Gateway est deja lance
echo [2.1/4] Verification d'IB Gateway...
tasklist /FI "IMAGENAME eq ibgateway.exe" 2>NUL | find /I /N "ibgateway.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] IB Gateway est deja en cours d'execution
) else (
    echo [INFO] Lancement d'IB Gateway...
    if exist "%IBGATEWAY_PATH%" (
        REM Lancer IB Gateway avec le fichier de configuration
        start "IB Gateway - Boursicotor" "%IBGATEWAY_PATH%"
        echo [INFO] IB Gateway demarre, attente de la connexion...
        echo [INFO] Veuillez vous connecter manuellement dans IB Gateway
        echo.
        echo ========================================
        echo  IMPORTANT: Connectez-vous a IB Gateway
        echo  User: ericlapinasimu
        echo  Mode: Paper Trading (Simule)
        echo  Port API: 4002
        echo ========================================
        echo.
        echo Appuyez sur une touche une fois connecte...
        pause
    ) else (
        echo.
        echo ========================================
        echo  [ERREUR] IB Gateway non trouve !
        echo ========================================
        echo.
        echo IB Gateway n'a pas ete trouve a: %IBGATEWAY_PATH%
        echo.
        echo Veuillez verifier l'installation d'IB Gateway
        echo ou modifier le chemin dans ce script.
        echo.
        pause
        exit /b 1
    )
)

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
        timeout /t 2 /nobreak >NUL
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
        echo ou modifier le chemin dans ce script ^(ligne 51^).
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

streamlit run frontend/app.py

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
