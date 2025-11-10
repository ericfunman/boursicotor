"""
Script de test du StrategyAdapter
Teste la génération de signaux avec différentes stratégies
"""

from backend.models import SessionLocal, Strategy, Ticker, HistoricalData
from backend.strategy_adapter import StrategyAdapter
import pandas as pd

def test_strategy_adapter():
    """Teste l'adaptateur de stratégie"""
    db = SessionLocal()
    
    try:
        print("🧪 Test du StrategyAdapter\n")
        print("="*60)
        
        # 1. Lister toutes les stratégies
        strategies = db.query(Strategy).all()
        print(f"\n📋 {len(strategies)} stratégies trouvées dans la base de données:\n")
        
        for i, strat in enumerate(strategies, 1):
            strategy_info = StrategyAdapter.format_strategy_info(strat)
            print(f"{i}. {strat.name}")
            print(f"   Type: {strategy_info['type']}")
            print(f"   Simple: {strategy_info['is_simple']}")
            print(f"   Enhanced: {strategy_info['is_enhanced']}")
            print(f"   Indicateurs: {', '.join(strategy_info['indicators'])}")
            print()
        
        # 2. Charger des données de test
        print("="*60)
        print("\n📊 Chargement des données WLN (1min)...\n")
        
        ticker = db.query(Ticker).filter(Ticker.symbol == 'WLN').first()
        if not ticker:
            print("❌ Ticker WLN non trouvé")
            return
        
        records = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id,
            HistoricalData.interval == '1min'
        ).order_by(HistoricalData.timestamp.asc()).limit(500).all()
        
        if not records:
            print("❌ Aucune donnée historique pour WLN")
            return
        
        print(f"✅ {len(records)} records chargés")
        
        # Créer un DataFrame
        df = pd.DataFrame({
            'time': [rec.timestamp for rec in records],
            'open': [rec.open for rec in records],
            'high': [rec.high for rec in records],
            'low': [rec.low for rec in records],
            'close': [rec.close for rec in records],
            'volume': [rec.volume for rec in records]
        })
        
        # Calculer les indicateurs
        print("\n🔧 Calcul des indicateurs techniques...")
        from backend.technical_indicators import calculate_and_update_indicators
        df = calculate_and_update_indicators(df, save_to_db=False)
        print(f"✅ Indicateurs calculés (colonnes: {len(df.columns)})")
        
        # 3. Tester chaque stratégie
        print("\n" + "="*60)
        print("\n🎯 Test de génération de signaux:\n")
        
        for strat in strategies[:5]:  # Tester les 5 premières stratégies
            print(f"\n📊 Stratégie: {strat.name}")
            print(f"   Type: {strat.strategy_type}")
            
            try:
                signal_times, signal_prices, signal_types = StrategyAdapter.generate_signals(df, strat)
                
                buy_count = sum(1 for t in signal_types if t == 'buy')
                sell_count = sum(1 for t in signal_types if t == 'sell')
                
                print(f"   ✅ Signaux générés: {len(signal_times)} total")
                print(f"      - {buy_count} signaux d'achat")
                print(f"      - {sell_count} signaux de vente")
                
                # Signal actuel
                current_signal, current_color = StrategyAdapter.get_current_signal(df, strat)
                print(f"   Signal actuel: {current_signal} (couleur: {current_color})")
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*60)
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_strategy_adapter()
