@echo off
REM ========================================
REM  Diagnostic IB Gateway
REM ========================================

echo.
echo ========================================
echo  Diagnostic IB Gateway
echo ========================================
echo.

REM Vérifier les processus liés à IB Gateway
echo [1] Recherche des processus IB Gateway...
echo.

echo Processus Java:
tasklist /FI "IMAGENAME eq java.exe" 2>NUL | findstr "java.exe"
if "%ERRORLEVEL%"=="1" echo   Aucun processus Java trouvé

echo.
echo Processus IB Gateway:
tasklist /FI "IMAGENAME eq ibgateway.exe" 2>NUL | findstr "ibgateway.exe"
if "%ERRORLEVEL%"=="1" echo   Aucun processus ibgateway.exe trouvé

tasklist /FI "IMAGENAME eq ibgateway1.exe" 2>NUL | findstr "ibgateway1.exe"
if "%ERRORLEVEL%"=="1" echo   Aucun processus ibgateway1.exe trouvé

tasklist /FI "IMAGENAME eq javaw.exe" 2>NUL | findstr "javaw.exe"
if "%ERRORLEVEL%"=="1" echo   Aucun processus javaw.exe trouvé

echo.
echo [2] Test de connexion réseau...
echo.

REM Test de connexion au port 4002 (IB Gateway)
echo Test du port 4002 (IB Gateway):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', 4002); $tcp.Close(); Write-Host '✅ Port 4002 ouvert - IB Gateway accessible' } catch { Write-Host '❌ Port 4002 fermé - IB Gateway non accessible' }" 2>NUL

echo.
REM Test de connexion au port 7497 (TWS)
echo Test du port 7497 (TWS):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('127.0.0.1', 7497); $tcp.Close(); Write-Host '✅ Port 7497 ouvert - TWS accessible' } catch { Write-Host '❌ Port 7497 fermé - TWS non accessible' }" 2>NUL

echo.
echo [3] Chemins IB Gateway...
echo.

REM Vérifier les chemins d'installation courants
set IBGATEWAY_PATH1=C:\Jts\ibgateway\1037\ibgateway.exe
set IBGATEWAY_PATH2=C:\Jts\ibgateway\latest\ibgateway.exe
set IBGATEWAY_PATH3=C:\IB Gateway\ibgateway.exe

if exist "%IBGATEWAY_PATH1%" (
    echo ✅ Trouvé: %IBGATEWAY_PATH1%
) else (
    echo ❌ Non trouvé: %IBGATEWAY_PATH1%
)

if exist "%IBGATEWAY_PATH2%" (
    echo ✅ Trouvé: %IBGATEWAY_PATH2%
) else (
    echo ❌ Non trouvé: %IBGATEWAY_PATH2%
)

if exist "%IBGATEWAY_PATH3%" (
    echo ✅ Trouvé: %IBGATEWAY_PATH3%
) else (
    echo ❌ Non trouvé: %IBGATEWAY_PATH3%
)

echo.
echo [4] Recommandations...
echo.

echo Si IB Gateway ne démarre pas automatiquement:
echo 1. Lancez manuellement: C:\Jts\ibgateway\1037\ibgateway.exe
echo 2. Connectez-vous avec vos identifiants
echo 3. Choisissez "Paper Trading"
echo 4. Vérifiez que l'API est activée dans Configuration → API → Settings
echo 5. Ajoutez 127.0.0.1 aux IPs de confiance
echo.

echo Appuyez sur une touche pour continuer...
pause >nul