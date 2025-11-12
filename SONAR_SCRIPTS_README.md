# 🔄 Sonar Monitoring & Auto-Fixing Toolkit

Suite complète de scripts pour récupérer et corriger les issues SonarCloud en boucle.

---

## 📋 Table des Matières

1. [Scripts Disponibles](#scripts-disponibles)
2. [Installation](#installation)
3. [Modes d'Utilisation](#modes-dutilisation)
4. [Exemples](#exemples)
5. [Architecture](#architecture)

---

## 📁 Scripts Disponibles

### 1. `sonar_monitor.py` - Récupérateur d'Issues
**Récupère les issues et couverture depuis SonarCloud**

```bash
# Mode interactif (défaut)
python sonar_monitor.py

# Mode automatique (affiche le résumé une fois)
python sonar_monitor.py --auto

# Mode export JSON
python sonar_monitor.py --json
```

**Fonctionnalités**:
- ✅ Récupère toutes les issues SonarCloud
- ✅ Filtre par sévérité (BLOCKER, CRITICAL, MAJOR, etc.)
- ✅ Filtre par type (BUG, CODE_SMELL, VULNERABILITY)
- ✅ Affiche la couverture de test (locale et SonarCloud)
- ✅ Affiche les métriques de qualité
- ✅ Export en JSON pour traitement ultérieur

**Menu Interactif**:
```
1. Afficher les issues
2. Filtrer par sévérité
3. Filtrer par type
4. Afficher la couverture
5. Exporter en JSON
6. Rafraîchir les données
0. Quitter
```

### 2. `auto_fix_sonar.py` - Correcteur Automatique
**Propose et applique des corrections aux issues**

```bash
# Mode interactif
python auto_fix_sonar.py

# Mode sec (afficher sans appliquer)
python auto_fix_sonar.py --dry-run

# Mode automatique (batch)
python auto_fix_sonar.py --auto
```

**Types de Corrections Détectées**:
- 🔴 Bare except statements
- 📝 Print statements en production
- 📚 Missing docstrings
- 🔧 Too many function arguments
- 🗑️ Unused variables
- ❌ Unused imports
- 📋 Duplicate code
- 📏 Lines too long
- 🔢 Magic numbers
- 💬 Inconsistent quotes

### 3. `sonar_loop.py` - Gestionnaire Intégré (RECOMMANDÉ)
**Combine les deux scripts en une boucle interactive complète**

```bash
# Mode interactif complet (défaut)
python sonar_loop.py

# Mode batch (une exécution)
python sonar_loop.py --batch

# Mode watch (rafraîchit toutes les 60s)
python sonar_loop.py --watch

# Mode watch avec intervalle personnalisé
python sonar_loop.py --watch --interval 120
```

**Menu Principal**:
```
1. View all issues
2. Fix top issues
3. Run tests
4. Generate coverage report
5. View coverage details
6. Export report
7. Next iteration
0. Exit
```

---

## 🚀 Installation

### Prérequis
```bash
# Python 3.9+
python --version

# Dépendances
pip install requests pytest pytest-cov
```

### Installation des Scripts
```bash
# Les scripts sont déjà dans le répertoire racine
# Vérifier qu'ils existent
ls -la sonar_*.py
```

### Configuration (Optionnelle)
```bash
# Pour une meilleure limite API, définir le token
export SONAR_TOKEN="votre_token_sonarcloud"

# ou dans le script (sonar_monitor.py)
SONAR_TOKEN = "squ_..."
```

---

## 📖 Modes d'Utilisation

### Mode 1: Surveillance Rapide
```bash
# Afficher un résumé rapide une fois
python sonar_monitor.py --auto

# Résultat:
# - Nombre d'issues par sévérité
# - Couverture de test
# - Métriques de qualité
# - Top 10 des règles les plus violées
```

### Mode 2: Analyse Interactive
```bash
# Explorer les issues en détail
python sonar_monitor.py

# Puis:
# [1] Afficher tous les issues
# [2] Filtrer par sévérité (ex: CRITICAL)
# [3] Filtrer par type (ex: CODE_SMELL)
# [5] Exporter en JSON pour analyse
```

### Mode 3: Correction Guidée (Recommandé)
```bash
# Boucle interactive avec correction proposée
python sonar_loop.py

# À chaque itération:
# 1. Affiche les issues actuelles
# 2. Affiche la tendance (amélioration/dégradation)
# 3. Propose des actions:
#    - Lister les issues
#    - Proposer des fixes
#    - Lancer les tests
#    - Générer la couverture
# 4. Passer à l'itération suivante
```

### Mode 4: Suivi Continu
```bash
# Rafraîchit toutes les 60 secondes
python sonar_loop.py --watch

# Résultat:
# ⏰ Check #1 - 14:32:15
# 📋 Issues: 45
#    Blocker: 1
#    Critical: 3
#    Major: 12
# 📈 Coverage: 45%
# ⏳ Next check in 60s...
```

### Mode 5: Batch Reporting
```bash
# Génère un rapport JSON une fois
python sonar_loop.py --batch

# Fichier généré: sonar_batch_report.json
# Contient: issues, couverture, timestamp
```

---

## 💡 Exemples

### Exemple 1: Trouver tous les BLOCKER
```bash
$ python sonar_monitor.py

Menu> 2
Sévérité> BLOCKER

# Résultat: Liste des issues BLOCKER
```

### Exemple 2: Corriger les Code Smells
```bash
$ python sonar_loop.py

Actions> 2
# Affiche les top issues par règle
# Propose des corrections

# Puis manuellement:
1. Ouvrir le fichier concerné
2. Appliquer la correction suggérée
3. Sauvegarder
4. Commit et push
5. Retour à sonar_loop, action 7 (Next iteration)
```

### Exemple 3: Augmenter la Couverture
```bash
$ python sonar_loop.py

Actions> 4
# Génère un nouveau coverage.xml

Actions> 5
# Affiche les détails de couverture:
#   Lines valid:   8908
#   Lines covered: 488
#   Rate:          5.48%
```

### Exemple 4: Export pour Dashboard
```bash
$ python sonar_monitor.py

Menu> 5
# Génère sonar_report.json

# Puis utiliser le JSON pour:
# - Dashboard personnel
# - Alertes personnalisées
# - Intégration avec d'autres outils
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      sonar_loop.py (ENTRY POINT)        │
│     Gestionnaire Intégré Principal       │
└─────────────────────────────────────────┘
            ↓                  ↓
    ┌───────────────┐  ┌──────────────────┐
    │ sonar_monitor │  │  auto_fix_sonar  │
    │   + Coverage  │  │ + Suggestions    │
    └───────────────┘  └──────────────────┘
            ↓                  ↓
    ┌───────────────────────────────────┐
    │   SonarCloud API (REST)           │
    │  + Local coverage.xml             │
    │  + pytest integration             │
    └───────────────────────────────────┘
```

### Flux d'Exécution
```
1. Récupérer issues SonarCloud (API)
2. Récupérer couverture locale (XML)
3. Grouper par règle/sévérité
4. Afficher résumé + tendances
5. Menu interactif (action utilisateur)
6. Proposer corrections (automatique)
7. Lancer tests si demandé
8. Générer nouveau coverage si demandé
9. Retour étape 1 (boucle)
```

---

## 📊 Formats de Sortie

### JSON Report (sonar_report.json)
```json
{
  "timestamp": "2025-11-10T14:32:15.123456",
  "project": "ericfunman_boursicotor",
  "organization": "ericfunman",
  "issues_count": 45,
  "issues": [
    {
      "key": "AVN_U...",
      "type": "CODE_SMELL",
      "severity": "MAJOR",
      "rule": "python:S1234",
      "message": "Print statement found",
      "component": "backend/backtesting_engine.py",
      "line": 1986,
      "debt": "5min"
    }
  ],
  "coverage": {...},
  "metrics": {...}
}
```

### Loop Report (sonar_loop_report.json)
```json
{
  "iterations": 3,
  "history": [
    {
      "iteration": 1,
      "timestamp": "2025-11-10T14:30:00",
      "issues_count": 48,
      "coverage": {...}
    },
    {
      "iteration": 2,
      "timestamp": "2025-11-10T14:31:00",
      "issues_count": 45,
      "coverage": {...}
    }
  ],
  "latest_issues_count": 45,
  "latest_coverage": {...}
}
```

---

## 🎯 Workflow Recommandé

### Phase 1: Diagnostic Initial
```bash
# Voir l'état complet
python sonar_monitor.py --auto

# Exporter les données
python sonar_monitor.py --json
```

### Phase 2: Correction Interactive
```bash
# Boucle interactive avec suggestions
python sonar_loop.py

# À chaque étape:
# 1. Voir les issues
# 2. Proposer fixes
# 3. Lancer tests
# 4. Générer couverture
# 5. Passage à l'itération suivante
```

### Phase 3: Suivi Continu
```bash
# Rafraîchir automatiquement
python sonar_loop.py --watch --interval 30
```

### Phase 4: Rapports
```bash
# Générer un rapport batch final
python sonar_loop.py --batch

# Analyser le JSON généré
cat sonar_batch_report.json | jq '.issues_count'
```

---

## ⚡ Tips & Tricks

### 1. Combiner avec Git
```bash
# Après chaque correction
git add .
git commit -m "fix: [sonar rule] description"
git push

# Puis refraîchir dans sonar_loop
```

### 2. Exporter pour Notification
```bash
# Générer un rapport
python sonar_monitor.py --json

# Puis parser le JSON pour envoyer une alerte
python -c "import json; data=json.load(open('sonar_report.json')); print(f'Issues: {data[\"issues_count\"]}')"
```

### 3. Intégrer dans CI/CD
```yaml
# .github/workflows/sonar-check.yml
- name: Check SonarCloud Issues
  run: python sonar_monitor.py --auto
```

### 4. Automatiser les Corrections Simples
```bash
# Avant d'utiliser auto_fix_sonar
# Mettre en place des pre-commit hooks:

# .git/hooks/pre-commit
python auto_fix_sonar.py --dry-run
```

---

## 🐛 Troubleshooting

### "❌ Erreur API"
```
Cause: Connexion SonarCloud échouée
Solution:
1. Vérifier la connexion internet
2. Vérifier le token (si utilisé)
3. Vérifier la clé du projet (ericfunman_boursicotor)
4. Retenter dans quelques secondes
```

### "Aucune issue trouvée"
```
Cause: Le projet n'existe pas ou pas d'accès
Solution:
1. Vérifier https://sonarcloud.io/projects
2. Vérifier que le projet est public
3. Vérifier les paramètres SONAR_PROJECT_KEY, SONAR_ORGANIZATION
```

### "No coverage.xml found"
```
Cause: Pas de fichier de couverture généré
Solution:
1. Lancer: python sonar_loop.py
2. Action 4: Generate coverage report
3. Cela lancera pytest avec --cov-report=xml
```

---

## 📚 Ressources

- [SonarCloud API Docs](https://sonarcloud.io/web_api_v2)
- [SonarCloud Issues Search](https://sonarcloud.io/api/issues/search)
- [Coverage.py Docs](https://coverage.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)

---

## 📝 Notes de Version

### v1.0 (2025-11-10)
- ✅ Script de récupération d'issues SonarCloud
- ✅ Analyse de couverture locale et SonarCloud
- ✅ Suggestions de correction automatique
- ✅ Boucle interactive intégrée
- ✅ Mode watch pour suivi continu
- ✅ Export JSON pour rapports

---

**Créé**: 2025-11-10  
**Auteur**: GitHub Copilot  
**Statut**: ✅ Production Ready

