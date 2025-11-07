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

REM Verifier si IB Gateway est deja lance (plusieurs processus possibles)
echo [2.1/4] Verification d'IB Gateway...
tasklist /FI "IMAGENAME eq java.exe" 2>NUL | find /I /N "java.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found
tasklist /FI "IMAGENAME eq ibgateway.exe" 2>NUL | find /I /N "ibgateway.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found
tasklist /FI "IMAGENAME eq ibgateway1.exe" 2>NUL | find /I /N "ibgateway1.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found
tasklist /FI "IMAGENAME eq javaw.exe" 2>NUL | find /I /N "javaw.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found

REM Essayer de se connecter au port IBKR pour verifier
echo [INFO] Test de connexion au port 4002 (IB Gateway)...
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', 4002); $tcp.Close(); exit 0 } catch { exit 1 }" 2>NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found

REM IB Gateway n'est pas lance
goto :gateway_not_found

:gateway_found
echo [OK] IB Gateway est deja en cours d'execution
goto :skip_ibgateway

:gateway_not_found

REM IB Gateway n'est pas lance - demander lancement manuel
echo.
echo ========================================
echo  IB Gateway requis
echo ========================================
echo.
echo [INFO] IB Gateway n'est pas lance.
echo.
echo VEUILLEZ LANCER IB GATEWAY MANUELLEMENT :
echo 1. Double-cliquez sur l'icone IB Gateway sur votre bureau
echo    OU lancez : C:\Jts\ibgateway\1037\ibgateway.exe
echo 2. Connectez-vous avec vos identifiants (ericlapinasimu)
echo 3. Choisissez Paper Trading
echo 4. Laissez IB Gateway ouvert
echo.
echo Une fois connecte, appuyez sur une touche pour continuer...
pause >nul

REM Verifier que Gateway est bien lance
tasklist /FI "IMAGENAME eq java.exe" 2>NUL | find /I /N "java.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_detected
tasklist /FI "IMAGENAME eq ibgateway.exe" 2>NUL | find /I /N "ibgateway.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_detected
tasklist /FI "IMAGENAME eq ibgateway1.exe" 2>NUL | find /I /N "ibgateway1.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_detected
tasklist /FI "IMAGENAME eq javaw.exe" 2>NUL | find /I /N "javaw.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_detected

REM Essayer de se connecter au port IBKR pour verifier
echo [INFO] Test de connexion au port 4002...
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', 4002); $tcp.Close(); exit 0 } catch { exit 1 }" 2>NUL
if "%ERRORLEVEL%"=="0" goto :gateway_detected

echo.
echo [ERREUR] IB Gateway n'est toujours pas detecte
echo Veuillez le lancer et reessayer
pause
exit /b 1

:gateway_detected
echo [OK] IB Gateway detecte - continuation du demarrage

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
        REM Utiliser cmd /c avec /k pour garder Redis en arriere-plan et fenetre persistante
        start "Redis Server - Boursicotor" cmd /k "cd /d C:\redis && redis-server.exe"
        echo [INFO] Attente du demarrage de Redis... (5 secondes)
        timeout /t 5 /nobreak >NUL
        
        REM Verifier que Redis repond avec redis-cli
        echo [INFO] Verification de la connexion Redis...
        C:\redis\redis-cli.exe ping > nul 2>&1
        if "%ERRORLEVEL%"=="0" (
            echo [OK] Redis demarre et en cours d'execution
        ) else (
            echo [INFO] Deuxieme tentative (attente 3 secondes)...
            timeout /t 3 /nobreak >NUL
            C:\redis\redis-cli.exe ping > nul 2>&1
            if "%ERRORLEVEL%"=="0" (
                echo [OK] Redis detecte !
            ) else (
                echo.
                echo ========================================
                echo  [ERREUR] Redis n'a pas pu demarrer
                echo ========================================
                echo.
                echo Verification manuelle:
                echo - Ouvrez le Gestionnaire des taches (Ctrl+Shift+Esc)
                echo - Cherchez "redis-server.exe" dans les processus
                echo.
                echo Si Redis est present mais ce script ne le detecte pas:
                echo - C'est peut-etre un probleme de timing Windows
                echo - Vous pouvez continuer et laisser Redis en arriere-plan
                echo.
                set /p CONTINUE="Voulez-vous continuer quand meme? (O/N): "
                if /i not "%CONTINUE%"=="O" (
                    exit /b 1
                )
            )
        )
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
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "celery">NUL
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
