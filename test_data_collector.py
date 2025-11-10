"""
Test du DataCollector avec Saxo Bank
"""
from backend.data_collector import DataCollector
from backend.config import logger, FRENCH_TICKERS

def test_data_collector():
    """Test la collecte et stockage de données"""
    print("=" * 60)
    print("💾 Test du DataCollector avec Saxo Bank")
    print("=" * 60)
    
    # Créer le collector
    collector = DataCollector(use_saxo=True)
    
    # Test 1: Collecter TotalEnergies
    print("\n" + "=" * 60)
    print("Test 1: Collecte TotalEnergies (TTE)")
    print("=" * 60)
    
    inserted = collector.collect_historical_data(
        symbol='TTE',
        name='TotalEnergies',
        duration='1D',
        bar_size='5min',
        exchange='EURONEXT'
    )
    
    print(f"\n✅ {inserted} enregistrements insérés")
    
    # Test 2: Récupérer les données de la base
    print("\n" + "=" * 60)
    print("Test 2: Récupération depuis la base de données")
    print("=" * 60)
    
    df = collector.get_latest_data('TTE', limit=10)
    
    if df is not None and len(df) > 0:
        print(f"\n✅ {len(df)} enregistrements récupérés")
        print("\nDernières données:")
        print(df.tail())
    else:
        print("\n⚠️ Aucune donnée en base")
    
    # Test 3: Collecter plusieurs tickers
    print("\n" + "=" * 60)
    print("Test 3: Collecte de 3 tickers français")
    print("=" * 60)
    
    tickers = [
        ('TTE', 'TotalEnergies'),
        ('MC', 'LVMH'),
        ('OR', 'L\'Oréal')
    ]
    
    collector.collect_multiple_tickers(
        tickers=tickers,
        duration='1D',
        bar_size='15min'
    )
    
    print("\n✅ Collecte terminée pour tous les tickers")
    
    # Test 4: Statistiques de la base
    print("\n" + "=" * 60)
    print("Test 4: Statistiques de la base de données")
    print("=" * 60)
    
    from backend.models import SessionLocal, Ticker, HistoricalData
    db = SessionLocal()
    
    ticker_count = db.query(Ticker).count()
    data_count = db.query(HistoricalData).count()
    
    print(f"\n📊 Statistiques:")
    print(f"   Tickers en base: {ticker_count}")
    print(f"   Points de données: {data_count}")
    
    # Détail par ticker
    print(f"\n   Détail par ticker:")
    for ticker in db.query(Ticker).all():
        count = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id
        ).count()
        print(f"      {ticker.symbol}: {count} points")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_data_collector()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
