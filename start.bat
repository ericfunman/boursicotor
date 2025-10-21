@echo off
echo ========================================
echo    Boursicotor - Plateforme de Trading
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Environnement virtuel non trouve!
    echo Veuillez d'abord executer: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo [2/3] Verification des dependances...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [WARNING] Dependances manquantes. Installation...
    pip install -r requirements.txt
)

REM Launch Streamlit app
echo [3/3] Lancement de Boursicotor...
echo.
echo ========================================
echo Application demarree sur http://localhost:8501
echo Appuyez sur Ctrl+C pour arreter
echo ========================================
echo.

streamlit run frontend\app.py

pause
