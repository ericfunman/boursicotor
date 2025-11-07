@echo off
REM ========================================
REM  Boursicotor - Launcher Script (SIMPLIFIE)
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
echo [1/5] Activation de l'environnement virtuel...
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

echo [2/5] Configuration detectee

REM Empecher la mise en veille pendant l'execution
echo [INFO] Desactivation temporaire de la mise en veille...
powercfg /change standby-timeout-ac 0 2>NUL
powercfg /change standby-timeout-dc 0 2>NUL
powercfg /change monitor-timeout-ac 0 2>NUL
powercfg /change monitor-timeout-dc 0 2>NUL
echo [OK] Mise en veille desactivee

REM ========== VERIFICATION IB GATEWAY ==========
set IBGATEWAY_PATH=C:\Jts\ibgateway\1037\ibgateway.exe

echo [3/5] Verification d'IB Gateway...
tasklist /FI "IMAGENAME eq java.exe" 2>NUL | find /I /N "java.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found
tasklist /FI "IMAGENAME eq ibgateway.exe" 2>NUL | find /I /N "ibgateway.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found
tasklist /FI "IMAGENAME eq ibgateway1.exe" 2>NUL | find /I /N "ibgateway1.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found
tasklist /FI "IMAGENAME eq javaw.exe" 2>NUL | find /I /N "javaw.exe">NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found

REM Essayer de se connecter au port IBKR pour verifier
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', 4002); $tcp.Close(); exit 0 } catch { exit 1 }" 2>NUL
if "%ERRORLEVEL%"=="0" goto :gateway_found

goto :gateway_not_found

:gateway_found
echo [OK] IB Gateway est deja en cours d'execution
goto :skip_ibgateway

:gateway_not_found
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

REM ========== VERIFICATION ET DEMARRAGE REDIS ==========
set REDIS_PATH=C:\redis\redis-server.exe

echo [4/5] Verification de Redis...

REM Verifier si Redis repond deja
C:\redis\redis-cli.exe ping > nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [OK] Redis est deja en cours d'execution et repond
    goto :redis_ok
)

REM Redis ne repond pas - le lancer
echo [INFO] Redis ne repond pas - lancement en cours...
if not exist "%REDIS_PATH%" (
    echo [ERREUR] Redis non trouve a: %REDIS_PATH%
    echo Veuillez installer Redis
    pause
    exit /b 1
)

REM Lancer Redis dans une fenetre persistante
start "Redis Server - Boursicotor" cmd /k "cd /d C:\redis && redis-server.exe"

REM Attendre le demarrage
echo [INFO] Attente du demarrage de Redis... (5 secondes)
timeout /t 5 /nobreak >NUL

REM Verifier que Redis repond
C:\redis\redis-cli.exe ping > nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [OK] Redis demarre et en cours d'execution
    goto :redis_ok
)

REM Deuxieme tentative
echo [INFO] Deuxieme tentative (attente 3 secondes)...
timeout /t 3 /nobreak >NUL
C:\redis\redis-cli.exe ping > nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [OK] Redis enfin detecte !
    goto :redis_ok
)

REM Redis n'a pas repondu
echo.
echo ========================================
echo  [ERREUR] Redis n'a pas pu demarrer
echo ========================================
echo.
set /p CONTINUE="Continuer quand meme? (O/N): "
if /i not "%CONTINUE%"=="O" (
    exit /b 1
)

:redis_ok

REM ========== VERIFICATION ET DEMARRAGE CELERY ==========
echo [5/5] Verification de Celery Worker...

tasklist /FI "IMAGENAME eq python.exe" 2>NUL | findstr /I "celery" > nul
if "%ERRORLEVEL%"=="0" (
    echo [OK] Celery Worker est deja en cours d'execution
) else (
    echo [INFO] Nettoyage et demarrage de Celery Worker...
    
    REM Flush Redis
    C:\redis\redis-cli.exe FLUSHALL > nul 2>&1
    
    REM Purge queue Celery
    cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && celery -A backend.celery_config purge -f" > nul 2>&1
    
    REM Nettoyage base de donnees
    cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && python cleanup_jobs.py" > nul 2>&1
    
    echo [OK] Nettoyage effectue
    
    REM Petit delai
    timeout /t 1 /nobreak >NUL
    
    REM Lancer Celery
    echo [INFO] Lancement de Celery Worker...
    start "Celery Worker - Boursicotor" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && celery -A backend.celery_config worker --loglevel=info --pool=solo"
    
    timeout /t 3 /nobreak >NUL
    echo [OK] Celery Worker demarre
)

REM ========== LANCER STREAMLIT ==========
echo.
echo ========================================
echo  Application en cours de demarrage...
echo  URL: http://localhost:8501
echo ========================================
echo.
echo IMPORTANT:
echo - Redis Server: Terminal separe ^(NE PAS FERMER^)
echo - Celery Worker: Terminal separe ^(NE PAS FERMER^)
echo - Streamlit: Cette fenetre
echo.
echo Appuyez sur Ctrl+C pour arreter Streamlit
echo.

"%~dp0venv\Scripts\streamlit.exe" run "%~dp0frontend\app.py"

REM Streamlit s'est arrete
echo.
echo ========================================
echo  Streamlit arrete
echo ========================================
echo.
echo ATTENTION: Redis et Celery sont toujours actifs
echo Fermez les fenetres Redis et Celery manuellement
echo.
pause
