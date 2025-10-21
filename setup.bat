@echo off
echo ========================================
echo    Configuration de Boursicotor
echo ========================================
echo.

echo [1/5] Creation de l'environnement virtuel...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Echec de creation de l'environnement virtuel
    pause
    exit /b 1
)

echo [2/5] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo [3/5] Mise a jour de pip...
python -m pip install --upgrade pip

echo [4/5] Installation des dependances...
echo.
echo NOTE: Si TA-Lib echoue, ce n'est pas grave.
echo Les indicateurs de base fonctionneront quand meme.
echo.
pip install -r requirements.txt

echo [5/5] Creation du fichier .env...
if not exist ".env" (
    copy .env.example .env
    echo [INFO] Fichier .env cree. Veuillez le configurer avec vos parametres.
) else (
    echo [INFO] Fichier .env existe deja.
)

echo.
echo ========================================
echo    Configuration terminee!
echo ========================================
echo.
echo Prochaines etapes:
echo 1. Editez le fichier .env avec vos parametres
echo 2. Creez la base de donnees PostgreSQL:
echo    psql -U postgres
echo    CREATE DATABASE boursicotor;
echo 3. Initialisez la base de donnees:
echo    python database\init_db.py
echo 4. Lancez l'application:
echo    start.bat
echo.
pause
