@echo off
REM Script de démarrage pour Boursicotor avec Celery

echo ========================================
echo   Boursicotor - Lancement avec Celery
echo ========================================
echo.

REM Vérifier que Redis tourne
echo [1/4] Vérification de Redis...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Redis ne répond pas!
    echo Lancez Redis d'abord :
    echo   - Via WSL: sudo service redis-server start
    echo   - Via Docker: docker start redis
    pause
    exit /b 1
)
echo OK: Redis opérationnel

echo.
echo [2/4] Lancement du Worker Celery...
start "Celery Worker" cmd /k "celery -A backend.celery_config worker --loglevel=info --pool=solo"
timeout /t 3 >nul

echo.
echo [3/4] Lancement de Flower (monitoring)...
start "Flower Monitoring" cmd /k "celery -A backend.celery_config flower"
timeout /t 2 >nul

echo.
echo [4/4] Lancement de Streamlit...
timeout /t 2 >nul
start "Streamlit App" cmd /k "streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"

echo.
echo ========================================
echo   Tous les services sont lancés!
echo ========================================
echo.
echo - Streamlit App: http://localhost:8501
echo - Flower Monitoring: http://localhost:5555
echo.
echo Fermez cette fenêtre pour arrêter tous les services.
pause
