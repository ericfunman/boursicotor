"""
Script pour remplacer les chaînes dupliquées dans frontend/app.py
Corrige les issues S1192 (CRITICAL)
"""
import re

# Read the file
with open('frontend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Track replacements
replacements = []

# Replace menu labels
old_str = '"📊 Dashboard"'
new_str = 'MENU_DASHBOARD'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"� Collecte de Données"'
new_str = 'MENU_DATA_COLLECTION'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"📈 Analyse Technique"'
new_str = 'MENU_TECHNICAL_ANALYSIS'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"🤖 Trading Automatique"'
new_str = 'MENU_AUTO_TRADING'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"📝 Passage d\'Ordres"'
new_str = 'MENU_ORDER_PLACEMENT'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"⚙️ Paramètres"'
new_str = 'MENU_SETTINGS'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

# Replace UI strings
old_str = '"🔄 Rafraîchir"'
new_str = 'BTN_REFRESH'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"Détails de l\'erreur"'
new_str = 'ERROR_DETAILS'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"Quantité"'
new_str = 'LABEL_QUANTITY'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

old_str = '"Prix (€)"'
new_str = 'LABEL_PRICE_EUR'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

# Replace hovermode (this is tricky - only replace in specific contexts)
old_str = "'x unified'"
new_str = 'HOVERMODE_X_UNIFIED'
count_before = content.count(old_str)
content = content.replace(old_str, new_str)
replacements.append(f"{old_str} -> {new_str}: {count_before} replacements")

# Write back
with open('frontend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Print summary
print("Replacements effectués:")
for r in replacements:
    print(f"  {r}")
print(f"\nTotal: {len(replacements)} types de chaînes remplacées")
