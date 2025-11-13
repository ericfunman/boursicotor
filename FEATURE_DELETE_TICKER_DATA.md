# 🗑️ Guide: Supprimer Données par Ticker

**Date:** November 13, 2025
**Feature:** Multi-select delete with preview

---

## 🎯 Nouvelle Fonctionnalité

La suppression de données est maintenant **facile et flexible**:

✅ Sélectionnez **1 seul ticker** → supprime juste ce ticker
✅ Sélectionnez **plusieurs tickers** → supprime tous à la fois
✅ Aperçu **avant suppression** → voir combien de points seront supprimés
✅ **Confirmation explicite** → pas de suppression accidentelle

---

## 📋 Étapes d'Utilisation

### 1️⃣ Aller à l'onglet "Données Collectées"

```
Streamlit UI:
├── Tableau des tickers collectés
├── Boutons d'action
└── Section de suppression ← ICI
```

### 2️⃣ Sélectionner un ou plusieurs tickers

**Vous verrez:**
```
┌──────────────────────────────────┐
│ Choisissez un ou plusieurs      │
│ tickers à supprimer:             │
│                                  │
│ ☐ TTE                           │
│ ☐ WLN                           │
│ ☐ TSL                           │
│ ☐ BNP                           │
│ [Select all / Clear]             │
└──────────────────────────────────┘
```

**Cliquez les checkboxes** pour sélectionner:
- ✅ **1 ticker:** Juste celui-ci sera supprimé
- ✅ **3 tickers:** Tous les 3 seront supprimés
- ✅ **Tous:** Vous pouvez tous les supprimer

### 3️⃣ Voir l'aperçu

**Après sélection, vous verrez:**
```
⚠️ APERÇU DES DONNÉES À SUPPRIMER:

TTE (Techniplas)                WLN (Weyland)
- Points: 1,234                 - Points: 567
- Période: 2025-11-10 à ...     - Période: 2025-11-05 à ...

⚠️ Total à supprimer: 1,801 points
```

### 4️⃣ Confirmer ou Annuler

```
[✅ Confirmer Suppression] [❌ Annuler]
```

- **Confirmer:** Les données sont supprimées immédiatement
- **Annuler:** Rien ne se passe, l'app recharge

### 5️⃣ Voir le résultat

```
✅ Suppression réussie!
1,801 points de données supprimés pour 2 ticker(s)

[Tableau rafraîchi avec les tickers restants]
```

---

## 💡 Exemples d'Utilisation

### Scénario 1: Supprimer 1 ticker
```
1. Sélectionnez: TTE
2. Aperçu: 1,234 points
3. Cliquez "Confirmer"
4. ✅ TTE supprimé, WLN et TSL restent
```

### Scénario 2: Supprimer 3 tickers à la fois
```
1. Sélectionnez: TTE, WLN, TSL
2. Aperçu: 1,234 + 567 + 890 = 2,691 points
3. Cliquez "Confirmer"
4. ✅ Tous les 3 supprimés en une opération
```

### Scénario 3: Supprimer tous les tickers
```
1. Cliquez "Select all"
2. Tous les tickers sont coché(s)
3. Aperçu: [total] points
4. Cliquez "Confirmer"
5. ✅ Toutes les données supprimées (la tableau devient vide)
```

---

## ⚠️ Important

### Avant de Supprimer

**✅ Bonnes pratiques:**
- Exportez vos données (CSV) avant suppression
- Vérifiez bien la liste des tickers à supprimer
- Lisez l'aperçu ("Total à supprimer")
- Lisez bien les périodes avant de confirmer

**❌ À ne pas faire:**
- Ne pas oublier que la suppression est **irréversible**
- Ne pas supprimer accidentellement les données dont vous avez besoin

---

## 🔄 Workflow Recommandé

```
1. 📊 Aller à "Données Collectées"
2. 📈 Regarder le tableau (voir ce que vous avez)
3. 💾 Exporter en CSV (sauvegarde de sécurité)
4. 🗑️ Sélectionner ce que vous voulez supprimer
5. 👀 Lire l'aperçu
6. ✅ Confirmer
7. 🎉 Voilà!
```

---

## 🆘 En Cas de Problème

### "Je vois pas le multi-select"
→ Rafraîchissez la page (F5 ou Ctrl+R)

### "Les données ne sont pas supprimées"
→ Vérifiez que vous aviez des données pour ce ticker
→ Vérifiez la console pour les messages d'erreur

### "J'ai supprimé les mauvaises données"
→ Désolé, les suppressions ne peuvent pas être annulées
→ Recollectez les données en relançant IBKR

---

## 📊 Bénéfices de cette Approach

✅ **Flexible:** 1, quelques, ou tous les tickers
✅ **Safe:** Aperçu avant suppression
✅ **Fast:** Multi-suppression en 1 clic
✅ **Clear:** Voir combien de points sont supprimés
✅ **Smart:** Grouper les suppressions

---

## 🎯 Résumé

```
AVANT (ancien):
- Pas de sélection individuelle
- Risque de tout supprimer accidentellement

MAINTENANT (nouveau):
✅ Multi-select (1, plusieurs, ou tous)
✅ Aperçu avant suppression
✅ Confirmation explicite
✅ Messages clairs
✅ Suppression sûre et contrôlée
```

---

**Status:** ✅ Ready to use
**Tested:** Yes
**Safe:** Yes (avec confirmation)

Enjoy! 🚀
