
"""Module documentation."""

import re

with open('frontend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove the col2 section with Résultat de la collecte
# This section starts with "with col2:" and ends before "# Data Overview tab"

pattern = r"        with col2:[\s\S]*?# Data Overview tab - Show all collected tickers in a table"
replacement = "    # Data Overview tab - Show all collected tickers in a table"

content_new = re.sub(pattern, replacement, content, count=1)

# Verify we made the change
if len(content_new) < len(content):
    with open('frontend/app.py', 'w', encoding='utf-8') as f:
        f.write(content_new)
    print("✅ Section 'Résultat de la collecte' supprimée")
    print(f"   Avant: {len(content)} chars")
    print(f"   Après: {len(content_new)} chars")
else:
    print("❌ Impossible de trouver la section")
