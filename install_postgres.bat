@echo off
echo ========================================
echo    Installation PostgreSQL avec Docker
echo ========================================
echo.

REM Vérifier si Docker est installé
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker n'est pas installé.
    echo.
    echo Téléchargez Docker Desktop depuis:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo ✅ Docker détecté
echo.

REM Arrêter et supprimer l'ancien conteneur s'il existe
echo Nettoyage des anciens conteneurs...
docker stop postgres-boursicotor 2>nul
docker rm postgres-boursicotor 2>nul

REM Créer et démarrer le conteneur PostgreSQL
echo.
echo 🚀 Création du conteneur PostgreSQL...
docker run --name postgres-boursicotor ^
    -e POSTGRES_PASSWORD=boursicotor2024 ^
    -e POSTGRES_DB=boursicotor ^
    -e POSTGRES_USER=boursicotor ^
    -p 5432:5432 ^
    -d postgres:15

if %errorlevel% equ 0 (
    echo.
    echo ✅ PostgreSQL démarré avec succès!
    echo.
    echo 📋 Informations de connexion:
    echo    Host: localhost
    echo    Port: 5432
    echo    Database: boursicotor
    echo    User: boursicotor
    echo    Password: boursicotor2024
    echo.
    echo 💡 Commandes utiles:
    echo    - Arrêter:  docker stop postgres-boursicotor
    echo    - Démarrer: docker start postgres-boursicotor
    echo    - Logs:     docker logs postgres-boursicotor
    echo.
) else (
    echo ❌ Erreur lors de la création du conteneur
    pause
    exit /b 1
)

REM Attendre que PostgreSQL soit prêt
echo ⏳ Attente du démarrage de PostgreSQL...
timeout /t 5 /nobreak >nul

REM Tester la connexion
echo.
echo 🔍 Test de connexion...
docker exec postgres-boursicotor pg_isready -U boursicotor

if %errorlevel% equ 0 (
    echo ✅ PostgreSQL est prêt!
) else (
    echo ⚠️  PostgreSQL démarre encore, attendez quelques secondes...
)

echo.
echo 📝 Mise à jour du fichier .env...
echo DB_TYPE=postgresql >> .env.tmp
echo DB_HOST=localhost >> .env.tmp
echo DB_PORT=5432 >> .env.tmp
echo DB_NAME=boursicotor >> .env.tmp
echo DB_USER=boursicotor >> .env.tmp
echo DB_PASSWORD=boursicotor2024 >> .env.tmp

echo.
echo ========================================
echo    Installation terminée!
echo ========================================
echo.
echo Prochaines étapes:
echo 1. Copiez les informations ci-dessus dans votre .env
echo 2. Exécutez: python database\init_db.py
echo 3. Démarrez l'application: streamlit run frontend\app.py
echo.
pause
