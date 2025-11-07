"""
Script pour vérifier les dates min/max de WLN et mettre à jour si nécessaire
"""
from backend.models import SessionLocal, Ticker as TickerModel, HistoricalData
from datetime import datetime

def check_wln_dates():
    """Vérifier les dates disponibles pour WLN"""
    db = SessionLocal()
    try:
        ticker = db.query(TickerModel).filter(TickerModel.symbol == 'WLN').first()
        
        if not ticker:
            print("❌ Ticker WLN non trouvé en base")
            return
        
        # Get min/max dates
        min_date = db.query(HistoricalData.timestamp).filter(
            HistoricalData.ticker_id == ticker.id
        ).order_by(HistoricalData.timestamp.asc()).first()
        
        max_date = db.query(HistoricalData.timestamp).filter(
            HistoricalData.ticker_id == ticker.id
        ).order_by(HistoricalData.timestamp.desc()).first()
        
        count = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id
        ).count()
        
        if min_date and max_date:
            print(f"✅ WLN - Données disponibles:")
            print(f"   📅 Date minimale: {min_date[0].strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"   📅 Date maximale: {max_date[0].strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"   📊 Nombre total de lignes: {count:,}")
            print(f"   ⏱️  Période couverte: {(max_date[0].date() - min_date[0].date()).days} jours")
            
            # Check if data is recent
            days_old = (datetime.now() - max_date[0]).days
            if days_old > 7:
                print(f"\n⚠️  ATTENTION: Les données ont {days_old} jours de retard!")
                print(f"   Dernière donnée: {max_date[0].strftime('%d/%m/%Y')}")
                print(f"   Date actuelle: {datetime.now().strftime('%d/%m/%Y')}")
                print(f"\n💡 Pour mettre à jour:")
                print(f"   1. Aller dans l'onglet 'Collecte de Données'")
                print(f"   2. Sélectionner WLN")
                print(f"   3. Cliquer sur 'Collecter les données'")
            else:
                print(f"\n✅ Données à jour (dernière collecte il y a {days_old} jour(s))")
        else:
            print("❌ Aucune donnée trouvée pour WLN")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_wln_dates()
