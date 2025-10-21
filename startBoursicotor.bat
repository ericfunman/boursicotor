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
echo [1/3] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Verifier si le fichier .env existe
if not exist ".env" (
    echo.
    echo [ATTENTION] Fichier .env non trouve !
    echo.
    echo Veuillez configurer vos credentials Saxo Bank dans .env
    echo Vous pouvez copier .env.example vers .env et le modifier.
    echo.
    pause
)

REM Verifier si les tokens Saxo Bank existent
if not exist ".saxo_tokens" (
    echo.
    echo [ATTENTION] Tokens Saxo Bank non trouves !
    echo.
    echo Vous devez d'abord vous authentifier avec : python authenticate_saxo.py
    echo.
    set /p AUTH="Voulez-vous vous authentifier maintenant ? (O/N): "
    if /i "%AUTH%"=="O" (
        echo.
        echo [2/3] Authentification Saxo Bank...
        python authenticate_saxo.py
        if errorlevel 1 (
            echo.
            echo [ERREUR] Authentification echouee !
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo.
        echo [INFO] Lancement en mode simulation (sans Saxo Bank)
        echo.
    )
) else (
    echo [2/3] Tokens Saxo Bank detectes
)

REM Lancer Streamlit
echo [3/3] Lancement de Boursicotor...
echo.
echo ========================================
echo  Application demarree !
echo  URL: http://localhost:8501
echo ========================================
echo.
echo Appuyez sur Ctrl+C pour arreter l'application
echo.

streamlit run frontend/app.py

REM Si Streamlit s'arrete
echo.
echo ========================================
echo  Application arretee
echo ========================================
echo.
pause
