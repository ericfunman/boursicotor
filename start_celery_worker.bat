@echo off
title Celery Worker - Boursicotor
cd /d %~dp0
echo ========================================
echo  Celery Worker - Boursicotor
echo ========================================
echo.
echo Activation environnement virtuel...
call venv\Scripts\activate.bat
echo.
echo Demarrage Celery Worker...
echo NE FERMEZ PAS CETTE FENETRE !
echo.
celery -A backend.celery_config worker --loglevel=info --pool=solo
echo.
echo Celery s'est arrete.
pause
