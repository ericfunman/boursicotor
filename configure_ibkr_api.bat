@echo off
REM Configure IB Gateway API settings to allow write access

echo Configuration de l'API IB Gateway...

REM Wait for IB Gateway settings folder to be created
timeout /t 5 /nobreak >nul

REM Find the Jts settings folder
for /d %%D in ("C:\Jts\Jts*") do (
    set "JTS_FOLDER=%%D"
    goto :found
)

:found
if not defined JTS_FOLDER (
    echo [ERREUR] Dossier de configuration IB Gateway non trouve
    exit /b 1
)

echo [INFO] Dossier de configuration: %JTS_FOLDER%

REM Create or update jts.ini to disable Read-Only API
echo [IBGateway] > "%JTS_FOLDER%\jts.ini"
echo WriteDebug=false >> "%JTS_FOLDER%\jts.ini"
echo TrustedIPs=127.0.0.1 >> "%JTS_FOLDER%\jts.ini"
echo ApiOnly=true >> "%JTS_FOLDER%\jts.ini"
echo LocalServerPort=4002 >> "%JTS_FOLDER%\jts.ini"
echo ReadOnlyApi=false >> "%JTS_FOLDER%\jts.ini"

echo [OK] API configuree en mode ecriture (Read-Only desactive)
exit /b 0
