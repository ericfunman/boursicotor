#!/usr/bin/env python3
"""
Migration: Ajoute la colonne isin à la table tickers
"""

import sqlite3
import os
from pathlib import Path

# Chemin de la DB
db_path = Path(__file__).parent / 'boursicotor.db'

if not db_path.exists():
    print(f"❌ Base de données non trouvée: {db_path}")
    exit(1)

print(f"📂 Base de données: {db_path}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(tickers);")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'isin' in columns:
        print("✅ Colonne 'isin' existe déjà")
    else:
        print("⏳ Ajout de la colonne 'isin'...")
        # SQLite ne peut pas ajouter UNIQUE directement, ajouter sans contrainte
        cursor.execute("""
            ALTER TABLE tickers 
            ADD COLUMN isin VARCHAR(12) DEFAULT NULL
        """)
        conn.commit()
        print("✅ Colonne 'isin' ajoutée (sans contrainte UNIQUE)")
    
    # Créer un index sur isin
    try:
        cursor.execute("CREATE UNIQUE INDEX idx_tickers_isin ON tickers(isin) WHERE isin IS NOT NULL;")
        conn.commit()
        print("✅ Index 'isin' créé")
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print("✅ Index 'isin' existe déjà")
        else:
            raise
    
    conn.close()
    print("\n✅ Migration terminée")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
