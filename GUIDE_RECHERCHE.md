# 🔍 Guide de Recherche d'Actions Françaises

## Présentation

La fonctionnalité de recherche vous permet de trouver facilement n'importe quelle action cotée sur Euronext Paris en tapant simplement son nom ou son ticker.

## Comment utiliser la recherche

### 1. Accéder à la page de collecte de données
- Lancez Boursicotor avec `startBoursicotor.bat`
- Dans le menu latéral, cliquez sur **"💾 Collecte de Données"**

### 2. Rechercher une action

Dans le champ de recherche en haut de la page, vous pouvez entrer :

#### **Par ticker** (recommandé pour la rapidité)
```
GLE          → Société Générale
MC           → LVMH
OR           → L'Oréal
TTE          → TotalEnergies
BNP          → BNP Paribas
AI           → Air Liquide
SAN          → Sanofi
```

#### **Par nom de société**
```
LVMH                 → LVMH Moet Hennessy Louis Vuitton
Total                → TotalEnergies SE
Société Générale     → Société Générale
L'Oreal              → L'Oréal SA
```

**Note :** La recherche fonctionne avec ou sans accents !
- ✅ "Société Générale" fonctionne
- ✅ "Societe Generale" fonctionne aussi

### 3. Sélectionner l'action

Une fois la recherche effectuée :
1. Les résultats s'affichent avec le **ticker**, le **nom complet**, et les **détails** (exchange, devise, UIC)
2. Cliquez sur **"Sélectionner"** à côté de l'action souhaitée
3. L'action apparaît dans la section "Action sélectionnée" 🎯

### 4. Collecter les données

Une fois l'action sélectionnée :
1. Choisissez la **durée** (1 jour, 5 jours, 1 mois)
2. Choisissez l'**intervalle** (1 min, 5 min, 15 min, 1 heure)
3. Cliquez sur **"📊 Collecter les données"**
4. Les données sont automatiquement récupérées et stockées dans la base de données

### 5. Visualiser les données

En bas de la page :
1. Sélectionnez le ticker à visualiser dans la liste déroulante
2. Cliquez sur **"📊 Afficher le graphique"**
3. Vous verrez :
   - Un graphique en chandeliers (candlestick)
   - Le volume des transactions
   - Les statistiques (prix actuel, plus haut, plus bas, variation)

## Exemples pratiques

### Exemple 1 : Collecter les données de Société Générale
1. Tapez "GLE" dans le champ de recherche
2. Cliquez sur "🔍 Rechercher"
3. Cliquez sur "Sélectionner" pour "GLE - Societe Generale"
4. Choisissez "1 mois" et "5 minutes"
5. Cliquez sur "📊 Collecter les données"

### Exemple 2 : Rechercher par nom de société
1. Tapez "LVMH" dans le champ de recherche
2. Cliquez sur "🔍 Rechercher"
3. Le résultat affiche "MC - LVMH Moet Hennessy Louis Vuitton"
4. Sélectionnez et collectez les données comme d'habitude

## Actions Françaises Populaires

Voici une liste des principales actions du CAC 40 :

| Ticker | Société | Secteur |
|--------|---------|---------|
| MC     | LVMH | Luxe |
| OR     | L'Oréal | Cosmétiques |
| TTE    | TotalEnergies | Énergie |
| SAN    | Sanofi | Pharmacie |
| AI     | Air Liquide | Gaz industriels |
| BNP    | BNP Paribas | Banque |
| GLE    | Société Générale | Banque |
| ACA    | Crédit Agricole | Banque |
| SU     | Schneider Electric | Industrie |
| CAP    | Capgemini | Services IT |
| CS     | AXA | Assurance |
| DG     | Vinci | Construction |
| BN     | Danone | Agroalimentaire |
| RI     | Pernod Ricard | Spiritueux |
| RMS    | Hermès | Luxe |
| KER    | Kering | Luxe |

## Astuces

### ✅ Bonnes pratiques
- Utilisez les **tickers** pour une recherche plus rapide et précise
- Les **caractères accentués** sont automatiquement normalisés
- La recherche est **insensible à la casse** (majuscules/minuscules)

### ⚠️ Limitations
- Seules les actions **cotées sur Euronext Paris** sont disponibles
- La recherche est limitée aux **20 premiers résultats**
- En mode simulation, l'API Saxo peut avoir des limitations

## Support

Pour plus d'informations sur l'API Saxo Bank :
- Documentation : https://www.developer.saxo/openapi/learn
- Support : https://www.developer.saxo/support

## Développement

Le code de recherche se trouve dans :
- `backend/saxo_search.py` - Logique de recherche
- `frontend/app.py` - Interface utilisateur (fonction `data_collection_page()`)

Pour tester la recherche en ligne de commande :
```bash
python backend\saxo_search.py
```
