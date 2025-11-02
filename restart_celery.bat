@echo off
echo ========================================
echo   Nettoyage et redemarrage Celery
echo ========================================

echo.
echo [1/5] Arret des processus existants...
taskkill /F /IM celery.exe 2>nul
taskkill /F /IM redis-server.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/5] Purge de la queue Celery...
cd /d %~dp0
celery -A backend.celery_config purge -f 2>nul

echo.
echo [3/5] Nettoyage Redis...
C:\redis\redis-cli.exe FLUSHALL 2>nul

echo.
echo [4/5] Demarrage Redis...
start "Redis Server" C:\redis\redis-server.exe
timeout /t 3 /nobreak >nul

echo.
echo [5/5] Demarrage Celery Worker...
start "Celery Worker - Boursicotor" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && celery -A backend.celery_config worker --loglevel=info --pool=solo"

echo.
echo ========================================
echo   Celery pret !
echo ========================================
echo.
echo Pour verifier l'etat:
echo   celery -A backend.celery_config inspect active
echo.
pause
