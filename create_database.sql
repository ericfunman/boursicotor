-- Script SQL pour créer la base de données Boursicotor
-- À exécuter dans SQL Shell (psql)

-- Se connecter en tant que postgres (mot de passe: bouh806)
-- Puis copier-coller ces commandes :

CREATE DATABASE boursicotor;

CREATE USER boursicotor WITH PASSWORD 'bouh806';

GRANT ALL PRIVILEGES ON DATABASE boursicotor TO boursicotor;

ALTER DATABASE boursicotor OWNER TO boursicotor;

-- Vérification
\l

-- Quitter
\q
