# 🚀 Guide d'installation PostgreSQL et Saxo Bank

## 📦 Option 1: Installation avec Docker (Recommandé)

### Prérequis
- Docker Desktop installé : https://www.docker.com/products/docker-desktop/

### Installation
1. **Exécuter le script d'installation** :
   ```bash
   install_postgres.bat
   ```

2. **Le script va** :
   - Créer un conteneur PostgreSQL
   - Configurer la base de données `boursicotor`
   - Créer l'utilisateur avec le mot de passe

3. **Informations de connexion** :
   - Host: `localhost`
   - Port: `5432`
   - Database: `boursicotor`
   - User: `boursicotor`
   - Password: `boursicotor2024`

### Commandes utiles
```bash
# Démarrer PostgreSQL
docker start postgres-boursicotor

# Arrêter PostgreSQL
docker stop postgres-boursicotor

# Voir les logs
docker logs postgres-boursicotor

# Se connecter à la base
docker exec -it postgres-boursicotor psql -U boursicotor -d boursicotor
```

---

## 📦 Option 2: Installation native Windows

### Téléchargement
1. Télécharger PostgreSQL 15+ : https://www.postgresql.org/download/windows/
2. Exécuter l'installeur
3. Définir un mot de passe pour l'utilisateur `postgres`
4. Noter le port (par défaut 5432)

### Configuration
1. Créer la base de données :
   ```bash
   createdb -U postgres boursicotor
   ```

2. Modifier le fichier `.env` :
   ```env
   DB_TYPE=postgresql
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=boursicotor
   DB_USER=postgres
   DB_PASSWORD=votre_mot_de_passe
   ```

---

## 🔧 Initialisation de la base de données

Une fois PostgreSQL installé et démarré :

```bash
# Initialiser les tables
python database\init_db.py

# Vérifier que tout fonctionne
python -c "from backend.models import SessionLocal; db = SessionLocal(); print('✅ Connexion OK')"
```

---

## 🏦 Configuration Saxo Bank API

### 1. Créer un compte développeur
1. Aller sur : https://www.developer.saxo/
2. Créer un compte développeur
3. Accéder au portail développeur

### 2. Créer une application
1. Dans le portail, créer une nouvelle application
2. Sélectionner le type : **OpenAPI**
3. Configurer les redirects URIs (pour OAuth)
4. Noter les informations :
   - **App Key** (Client ID)
   - **App Secret** (Client Secret)

### 3. Configurer l'environnement
Modifier le fichier `.env` :

```env
# Saxo Bank Configuration
SAXO_CLIENT_ID=votre_app_key
SAXO_CLIENT_SECRET=votre_app_secret
SAXO_APP_KEY=votre_app_key
SAXO_APP_SECRET=votre_app_secret
SAXO_BASE_URL=https://gateway.saxobank.com/sim/openapi  # Simulation
```

### 4. Obtenir un token d'accès

Saxo Bank utilise OAuth2. Voici le processus :

1. **Authorization URL** (ouvrir dans un navigateur) :
   ```
   https://sim.logonvalidation.saxobank.com/authorize
   ?client_id=YOUR_APP_KEY
   &response_type=code
   &redirect_uri=YOUR_REDIRECT_URI
   ```

2. **Échanger le code contre un token** :
   ```python
   import requests
   
   response = requests.post(
       'https://sim.logonvalidation.saxobank.com/token',
       data={
           'grant_type': 'authorization_code',
           'code': 'CODE_RECU',
           'redirect_uri': 'YOUR_REDIRECT_URI',
           'client_id': 'YOUR_APP_KEY',
           'client_secret': 'YOUR_APP_SECRET'
       }
   )
   
   token_data = response.json()
   access_token = token_data['access_token']
   refresh_token = token_data['refresh_token']
   ```

3. **Stocker les tokens de manière sécurisée**

### 5. Tester la connexion

```python
from brokers.saxo_client import saxo_client

# Se connecter
if saxo_client.connect():
    print("✅ Connexion Saxo Bank OK")
    
    # Tester la récupération de données
    data = saxo_client.get_historical_data("TTE", "1D", "5min")
    print(f"Données récupérées: {len(data)} lignes")
else:
    print("❌ Échec de connexion")
```

---

## 🔐 Sécurité

### Variables d'environnement sensibles
Ne **JAMAIS** commiter le fichier `.env` dans Git !

Le fichier `.gitignore` contient déjà :
```
.env
*.env
```

### Bonnes pratiques
1. Utiliser des tokens avec durée de vie limitée
2. Implémenter le refresh token automatique
3. Utiliser l'environnement de simulation pour les tests
4. Stocker les tokens de manière sécurisée (pas en clair)

---

## 📊 Symboles Saxo Bank

Saxo Bank utilise des **UIC (Unique Instrument Code)** :

| Symbole | Nom | UIC |
|---------|-----|-----|
| TTE | TotalEnergies | 15766 |
| WLN | Worldline | 15945 |
| MC | LVMH | 15875 |
| OR | L'Oréal | 15878 |
| AIR | Airbus | 15792 |
| SAN | Sanofi | 15880 |
| BNP | BNP Paribas | 15770 |
| SU | Schneider | 15885 |

Pour trouver d'autres UIC :
1. API : `/ref/v1/instruments`
2. Documentation : https://www.developer.saxo/openapi/referencedocs

---

## 🚀 Démarrage complet

```bash
# 1. Installer PostgreSQL
install_postgres.bat

# 2. Initialiser la base
python database\init_db.py

# 3. Configurer Saxo Bank dans .env

# 4. Démarrer l'application
streamlit run frontend\app.py
```

---

## 📝 Checklist

- [ ] PostgreSQL installé et démarré
- [ ] Base de données `boursicotor` créée
- [ ] Fichier `.env` configuré avec PostgreSQL
- [ ] Tables initialisées (`python database\init_db.py`)
- [ ] Compte développeur Saxo Bank créé
- [ ] Application Saxo Bank configurée
- [ ] Tokens d'accès obtenus
- [ ] Fichier `.env` configuré avec Saxo Bank
- [ ] Test de connexion Saxo Bank réussi
- [ ] Application Streamlit lancée

---

## 🆘 Dépannage

### PostgreSQL ne démarre pas
```bash
# Vérifier que le port 5432 n'est pas déjà utilisé
netstat -an | findstr 5432

# Voir les logs Docker
docker logs postgres-boursicotor
```

### Erreur de connexion PostgreSQL
```bash
# Tester la connexion
docker exec postgres-boursicotor pg_isready -U boursicotor

# Se connecter manuellement
docker exec -it postgres-boursicotor psql -U boursicotor -d boursicotor
```

### Saxo Bank : 401 Unauthorized
- Vérifier que les tokens sont valides
- Régénérer un nouveau token
- Vérifier les permissions de l'application

### Saxo Bank : 429 Too Many Requests
- Respecter les limites de l'API
- Implémenter un rate limiting
- Utiliser le cache pour les données historiques
