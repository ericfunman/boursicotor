@echo off
echo ========================================
echo    Installation PostgreSQL pour Boursicotor
echo ========================================
echo.

REM Vérifier si PostgreSQL est déjà installé
where psql >nul 2>&1
if %errorlevel% equ 0 (
    echo PostgreSQL semble déjà installé.
    echo Vérification de la version...
    psql --version
    goto :setup_db
)

echo PostgreSQL n'est pas installé.
echo.
echo Options d'installation:
echo 1. Télécharger et installer PostgreSQL depuis postgresql.org
echo 2. Utiliser Docker (recommandé pour le développement)
echo 3. Utiliser WSL avec Ubuntu
echo.
echo Pour une installation rapide avec Docker:
echo docker run --name postgres-boursicotor -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=boursicotor -p 5432:5432 -d postgres:15
echo.
pause

:setup_db
echo.
echo Configuration de la base de données...
echo.

REM Créer la base de données si elle n'existe pas
echo Tentative de création de la base de données 'boursicotor'...
createdb boursicotor 2>nul
if %errorlevel% equ 0 (
    echo ✅ Base de données 'boursicotor' créée avec succès
) else (
    echo ⚠️  La base de données 'boursicotor' existe peut-être déjà ou vous n'avez pas les permissions
)

echo.
echo Configuration terminée!
echo.
echo Modifiez le fichier .env avec vos identifiants PostgreSQL:
echo DB_HOST=localhost
echo DB_PORT=5432
echo DB_NAME=boursicotor
echo DB_USER=postgres
echo DB_PASSWORD=votre_mot_de_passe
echo.
pause