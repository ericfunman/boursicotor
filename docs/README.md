# 📚 Documentation - Boursicotor

Bienvenue dans la documentation du projet Boursicotor !

## 📖 Guides Disponibles

### 🚀 Pour Commencer

| Fichier | Description | Pour qui ? |
|---------|-------------|------------|
| **QUICK_START_LIVE_PAGE.md** | Guide de démarrage rapide avec interface visuelle | Utilisateurs |
| **TEST_GUIDE.md** | Procédure de test complète (17 tests) | Testeurs |

### 📊 Fonctionnalités de la Page Cours Live

| Fichier | Description | Détails |
|---------|-------------|---------|
| **README_LIVE_PAGE.md** | Vue d'ensemble complète | Architecture, exemples, améliorations futures |
| **LIVE_PAGE_FEATURES.md** | Documentation détaillée des 3 nouvelles fonctionnalités | Guide d'utilisation, création de stratégies |
| **CHANGELOG_LIVE_PAGE.md** | Changelog technique avec code avant/après | Développeurs |

### 📝 Résumés de Session

| Fichier | Description | Date |
|---------|-------------|------|
| **SESSION_SUMMARY_20241031.md** | Résumé complet de la session du 31 Oct 2024 | 31/10/2024 |

### 🔌 Intégration IBKR/Lynx

| Fichier | Description | Statut |
|---------|-------------|--------|
| **IBKR_INTEGRATION.md** | Guide complet d'intégration IBKR/Lynx API | En attente de test |

---

## 🎯 Les 3 Nouvelles Fonctionnalités de la Page Cours Live

### 1. 📊 Chargement des Données Historiques
Charge automatiquement toutes les données historiques depuis la base de données au démarrage.

**Lire :** `LIVE_PAGE_FEATURES.md` section 1

### 2. 🎯 Sélecteur de Stratégie
Permet de sélectionner une stratégie de trading pour générer des signaux d'achat/vente.

**Lire :** `LIVE_PAGE_FEATURES.md` section 2

### 3. 📈 Visualisation et Analyse des Signaux
Affiche les signaux historiques sur le graphique et analyse les performances de la stratégie.

**Lire :** `LIVE_PAGE_FEATURES.md` section 3

---

## 🚀 Démarrage Rapide (3 étapes)

### Étape 1 : Créer les Stratégies
```bash
python create_example_strategy.py
```

### Étape 2 : Lancer l'Application
```bash
streamlit run frontend/app.py
```

### Étape 3 : Tester
1. Aller dans "📊 Cours Live"
2. Sélectionner "RSI + MACD Momentum"
3. Sélectionner un ticker (ex: WLN)
4. Cliquer sur "▶️ Démarrer"

**→ Lire le guide complet :** `QUICK_START_LIVE_PAGE.md`

---

## 📁 Structure de la Documentation

```
docs/
├── README.md                    ← Ce fichier
│
├── 🚀 Guides de Démarrage
│   ├── QUICK_START_LIVE_PAGE.md     → Guide visuel rapide
│   └── TEST_GUIDE.md                 → Tests complets
│
├── 📊 Documentation Fonctionnelle
│   ├── README_LIVE_PAGE.md           → Vue d'ensemble
│   ├── LIVE_PAGE_FEATURES.md         → Fonctionnalités détaillées
│   └── CHANGELOG_LIVE_PAGE.md        → Changelog technique
│
├── 📝 Historique
│   └── SESSION_SUMMARY_20241031.md   → Résumé 31 Oct 2024
│
└── 🔌 Intégrations
    └── IBKR_INTEGRATION.md           → Guide IBKR/Lynx
```

---

## 🎓 Ordre de Lecture Recommandé

### Pour les Utilisateurs
1. **QUICK_START_LIVE_PAGE.md** : Démarrage rapide
2. **LIVE_PAGE_FEATURES.md** : Comprendre les fonctionnalités
3. **README_LIVE_PAGE.md** : Aller plus loin
4. **TEST_GUIDE.md** : Valider le bon fonctionnement

### Pour les Développeurs
1. **SESSION_SUMMARY_20241031.md** : Contexte des modifications
2. **CHANGELOG_LIVE_PAGE.md** : Détails techniques
3. **README_LIVE_PAGE.md** : Architecture complète
4. **IBKR_INTEGRATION.md** : Prochaines intégrations

---

## 📊 Statistiques de la Documentation

- **Total de fichiers** : 7 fichiers Markdown
- **Lignes de documentation** : ~1,800 lignes
- **Sections** : ~150 sections
- **Exemples de code** : ~40 exemples
- **Diagrammes** : ~10 diagrammes ASCII

---

## 🔍 Recherche Rapide

### Par Sujet

**Chargement de données historiques**
- `README_LIVE_PAGE.md` → Section "Chargement des Données Historiques"
- `CHANGELOG_LIVE_PAGE.md` → Modification 1

**Stratégies de trading**
- `LIVE_PAGE_FEATURES.md` → Section "Sélecteur de Stratégie"
- `QUICK_START_LIVE_PAGE.md` → Section "Configuration Avancée"

**Signaux d'achat/vente**
- `LIVE_PAGE_FEATURES.md` → Section "Affichage des Signaux"
- `README_LIVE_PAGE.md` → Section "Visualisation des Signaux"

**Analyse de performance**
- `README_LIVE_PAGE.md` → Section "Analyse de Performance"
- `TEST_GUIDE.md` → Tests 11-12

**IBKR/Lynx API**
- `IBKR_INTEGRATION.md` → Guide complet
- `SESSION_SUMMARY_20241031.md` → Mentions

---

## 🆘 FAQ

### Q : Comment créer ma propre stratégie ?
**R :** Consultez `LIVE_PAGE_FEATURES.md` section "Exemple de Stratégie dans la Base de Données"

### Q : Pourquoi "Aucune donnée historique" ?
**R :** Utilisez "Collecte de Données" pour générer des données. Voir `TEST_GUIDE.md` Test 2

### Q : Comment interpréter les signaux ?
**R :** Voir `QUICK_START_LIVE_PAGE.md` section "Interprétation des Signaux"

### Q : Où sont les fichiers Python modifiés ?
**R :** `CHANGELOG_LIVE_PAGE.md` liste tous les fichiers modifiés avec détails

### Q : Comment tester toutes les fonctionnalités ?
**R :** Suivez `TEST_GUIDE.md` avec les 17 tests

---

## 🐛 Dépannage

**Problème : Impossible de trouver un fichier**
- Tous les fichiers sont dans le dossier `docs/`
- Utilisez la recherche de votre éditeur (Ctrl+F)

**Problème : Lien cassé**
- Tous les liens internes référencent des fichiers existants
- Vérifiez que vous êtes dans le bon dossier

**Problème : Information manquante**
- Consultez plusieurs fichiers pour une vue complète
- Utilisez la section "Recherche Rapide" ci-dessus

---

## 📞 Support

### Avant de poser une question

1. ✅ Lisez `QUICK_START_LIVE_PAGE.md`
2. ✅ Consultez `TEST_GUIDE.md` section "Problèmes Courants"
3. ✅ Cherchez dans la documentation (Ctrl+F)

### Si le problème persiste

1. Vérifiez les logs de l'application
2. Examinez la base de données
3. Consultez `CHANGELOG_LIVE_PAGE.md` pour les détails techniques

---

## 🎯 Prochaines Documentations Prévues

- [ ] Guide de création de stratégies avancées
- [ ] Documentation de l'API IBKR/Lynx après tests
- [ ] Guide d'optimisation de paramètres
- [ ] Tutoriel backtesting complet
- [ ] Guide de déploiement en production

---

## 📅 Historique des Mises à Jour

| Date | Version | Modifications | Fichiers |
|------|---------|---------------|----------|
| 31/10/2024 | 1.0.0 | Création documentation complète Page Cours Live | 7 fichiers |

---

## 🌟 Contributions

Cette documentation a été créée pour faciliter l'utilisation et le développement du projet Boursicotor.

Si vous trouvez des erreurs ou souhaitez ajouter des informations, n'hésitez pas à modifier les fichiers Markdown.

---

**Bonne lecture ! 📚🚀**

---

## 🔗 Liens Utiles

### Documentation Externe
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Documentation](https://plotly.com/python/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [IBKR API Documentation](https://interactivebrokers.github.io/tws-api/)

### Ressources Trading
- [Investopedia - RSI](https://www.investopedia.com/terms/r/rsi.asp)
- [Investopedia - MACD](https://www.investopedia.com/terms/m/macd.asp)
- [Trading Strategies](https://www.investopedia.com/trading-strategies-4689645)

---

**Dernière mise à jour : 31 Octobre 2024**
