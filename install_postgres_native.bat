@echo off
echo ========================================
echo    Installation PostgreSQL Native
echo ========================================
echo.

echo Docker n'est pas installé. Installation native recommandée.
echo.
echo 📥 Étapes d'installation:
echo.
echo 1. Téléchargez PostgreSQL 15 depuis:
echo    https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
echo.
echo 2. Exécutez l'installeur
echo    - Choisissez le répertoire d'installation
echo    - Définissez un mot de passe pour l'utilisateur postgres
echo    - Port par défaut: 5432
echo    - Locale: French, France
echo.
echo 3. Après installation, créez la base de données:
echo.
echo    Ouvrez "SQL Shell (psql)" et tapez:
echo    Password: [votre mot de passe]
echo    CREATE DATABASE boursicotor;
echo    CREATE USER boursicotor WITH PASSWORD 'boursicotor2024';
echo    GRANT ALL PRIVILEGES ON DATABASE boursicotor TO boursicotor;
echo    \q
echo.
echo 4. Mettez à jour le fichier .env avec votre mot de passe
echo.
echo ========================================
echo.

REM Ouvrir le site de téléchargement
echo Voulez-vous ouvrir la page de téléchargement? (O/N)
set /p OPEN_BROWSER=

if /i "%OPEN_BROWSER%"=="O" (
    start https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
)

echo.
echo Une fois PostgreSQL installé, revenez ici et appuyez sur une touche...
pause

REM Test si PostgreSQL est accessible
echo.
echo 🔍 Test de connexion PostgreSQL...
psql --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL est installé!
    echo.
    echo Pour créer la base de données, exécutez:
    echo psql -U postgres -c "CREATE DATABASE boursicotor;"
    echo psql -U postgres -c "CREATE USER boursicotor WITH PASSWORD 'boursicotor2024';"
    echo psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE boursicotor TO boursicotor;"
    echo.
) else (
    echo ⚠️  PostgreSQL n'est pas encore dans le PATH
    echo Redémarrez le terminal après l'installation
)

echo.
echo ========================================
echo Configuration .env
echo ========================================
echo.
echo Assurez-vous que votre fichier .env contient:
echo.
echo DB_TYPE=postgresql
echo DB_HOST=localhost
echo DB_PORT=5432
echo DB_NAME=boursicotor
echo DB_USER=boursicotor
echo DB_PASSWORD=boursicotor2024
echo.
pause
