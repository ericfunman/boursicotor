"""
Test de collecte avec intervalles étendus et secondes
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backend.data_collector import DataCollector
from backend.config import logger


def test_extended_intervals():
    """Test des nouveaux intervalles disponibles"""
    
    print("\n" + "="*60)
    print("TEST DES INTERVALLES ÉTENDUS")
    print("="*60)
    
    # Test avec interval à la seconde (plus petit)
    print("\n🔍 Test 1: Collecte avec intervalle de 1 seconde")
    print("-" * 60)
    
    collector = DataCollector(use_saxo=True)
    
    try:
        inserted = collector.collect_historical_data(
            symbol="GLE",
            name="Société Générale",
            duration="1H",  # 1 heure
            bar_size="1sec"  # 1 seconde
        )
        
        if inserted > 0:
            print(f"✅ {inserted} enregistrements collectés avec succès (1 seconde)")
        else:
            print("ℹ️ Aucune nouvelle donnée (peut-être déjà en base)")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test avec intervalle moyen
    print("\n🔍 Test 2: Collecte avec intervalle de 5 secondes")
    print("-" * 60)
    
    try:
        inserted = collector.collect_historical_data(
            symbol="MC",
            name="LVMH",
            duration="4H",  # 4 heures
            bar_size="5sec"  # 5 secondes
        )
        
        if inserted > 0:
            print(f"✅ {inserted} enregistrements collectés avec succès (5 secondes)")
        else:
            print("ℹ️ Aucune nouvelle donnée (peut-être déjà en base)")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test avec longue période
    print("\n🔍 Test 3: Collecte avec longue période (6 mois)")
    print("-" * 60)
    
    try:
        inserted = collector.collect_historical_data(
            symbol="TTE",
            name="TotalEnergies",
            duration="6M",  # 6 mois
            bar_size="1day"  # 1 jour
        )
        
        if inserted > 0:
            print(f"✅ {inserted} enregistrements collectés avec succès (6 mois)")
        else:
            print("ℹ️ Aucune nouvelle donnée (peut-être déjà en base)")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "="*60)
    print("TESTS TERMINÉS")
    print("="*60)
    
    # Afficher les statistiques de la base
    from backend.models import SessionLocal, HistoricalData, Ticker
    db = SessionLocal()
    
    try:
        total_points = db.query(HistoricalData).count()
        total_tickers = db.query(Ticker).count()
        
        print(f"\n📊 Statistiques de la base de données:")
        print(f"   - Total tickers: {total_tickers}")
        print(f"   - Total points de données: {total_points:,}")
        
        print(f"\n📋 Détail par ticker:")
        for ticker in db.query(Ticker).all():
            count = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker.id
            ).count()
            print(f"   - {ticker.symbol}: {count:,} points")
            
    finally:
        db.close()


if __name__ == "__main__":
    test_extended_intervals()
