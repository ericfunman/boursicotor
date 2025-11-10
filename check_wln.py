
"""Module documentation."""

import sys
sys.path.insert(0, '.')
from backend.models import Ticker, SessionLocal

db = SessionLocal()
ticker = db.query(Ticker).filter(Ticker.symbol == 'WLN').first()

if ticker:
    print(f"✅ WLN existe en base")
    print(f"   ID: {ticker.id}")
    print(f"   Nom: {ticker.name}")
    print(f"   Exchange: {ticker.exchange}")
else:
    print("❌ WLN n'existe PAS en base de données")
    print("   Vous devez d'abord ajouter WLN via 'Collecte de Données'")

db.close()
