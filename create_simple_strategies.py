"""
Script pour ajouter des stratégies simples compatibles avec la page Cours Live
"""

from backend.models import SessionLocal, Strategy
import json

def create_simple_strategies():
    """Crée des stratégies simples supplémentaires"""
    db = SessionLocal()
    
    strategies_to_create = [
        {
            "name": "MACD Crossover",
            "description": "Stratégie basée uniquement sur le croisement MACD",
            "strategy_type": "momentum",
            "parameters": {
                "buy_conditions": "macd is not None and macd_signal is not None and macd > macd_signal",
                "sell_conditions": "macd is not None and macd_signal is not None and macd < macd_signal",
                "indicators": ["MACD"],
                "description": "Achat quand MACD croise au-dessus du signal, vente quand MACD croise en-dessous"
            }
        },
        {
            "name": "RSI Strict",
            "description": "Stratégie RSI avec seuils stricts (20/80)",
            "strategy_type": "mean_reversion",
            "parameters": {
                "buy_conditions": "rsi is not None and rsi < 20",
                "sell_conditions": "rsi is not None and rsi > 80",
                "indicators": ["RSI_14"],
                "description": "Achat en zone de survente extrême (RSI < 20), vente en zone de surachat extrême (RSI > 80)"
            }
        },
        {
            "name": "RSI Modéré",
            "description": "Stratégie RSI avec seuils modérés (40/60)",
            "strategy_type": "mean_reversion",
            "parameters": {
                "buy_conditions": "rsi is not None and rsi < 40",
                "sell_conditions": "rsi is not None and rsi > 60",
                "indicators": ["RSI_14"],
                "description": "Achat RSI < 40, vente RSI > 60 (génère plus de signaux)"
            }
        },
        {
            "name": "RSI + MACD Strict",
            "description": "Combinaison stricte RSI et MACD",
            "strategy_type": "momentum",
            "parameters": {
                "buy_conditions": "rsi is not None and macd is not None and macd_signal is not None and rsi < 35 and macd > macd_signal and macd > 0",
                "sell_conditions": "rsi is not None and macd is not None and macd_signal is not None and rsi > 65 and macd < macd_signal and macd < 0",
                "indicators": ["RSI_14", "MACD"],
                "description": "Achat: RSI < 35 ET MACD > Signal ET MACD positif. Vente: RSI > 65 ET MACD < Signal ET MACD négatif"
            }
        },
        {
            "name": "MACD Zéro Crossover",
            "description": "Achat quand MACD croise zéro vers le haut",
            "strategy_type": "momentum",
            "parameters": {
                "buy_conditions": "macd is not None and macd > 0 and macd_signal is not None",
                "sell_conditions": "macd is not None and macd < 0 and macd_signal is not None",
                "indicators": ["MACD"],
                "description": "Achat quand MACD devient positif, vente quand MACD devient négatif"
            }
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    try:
        for strat_data in strategies_to_create:
            # Vérifier si la stratégie existe déjà
            existing = db.query(Strategy).filter(Strategy.name == strat_data["name"]).first()
            
            if existing:
                print(f"⏭️  '{strat_data['name']}' existe déjà")
                skipped_count += 1
                continue
            
            # Créer la stratégie
            strategy = Strategy(
                name=strat_data["name"],
                description=strat_data["description"],
                strategy_type=strat_data["strategy_type"],
                parameters=json.dumps(strat_data["parameters"]),
                is_active=True
            )
            
            db.add(strategy)
            created_count += 1
            print(f"✅ '{strat_data['name']}' créée")
        
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ {created_count} nouvelles stratégies créées")
        print(f"⏭️  {skipped_count} stratégies déjà existantes")
        print(f"{'='*60}")
        
        # Afficher toutes les stratégies simples disponibles
        print("\n📋 Stratégies simples disponibles pour la page Cours Live:\n")
        all_strategies = db.query(Strategy).all()
        simple_count = 0
        
        for s in all_strategies:
            try:
                params = json.loads(s.parameters) if s.parameters else {}
                if 'buy_conditions' in params and 'sell_conditions' in params:
                    simple_count += 1
                    indicators = ', '.join(params.get('indicators', ['N/A']))
                    print(f"{simple_count}. {s.name}")
                    print(f"   Type: {s.strategy_type}")
                    print(f"   Indicateurs: {indicators}")
                    print(f"   Description: {s.description}")
                    print()
            except:
                pass
        
        print(f"Total: {simple_count} stratégies simples disponibles")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🎯 Création de stratégies simples pour la page Cours Live...\n")
    create_simple_strategies()
    print("\n✅ Terminé! Relancez Streamlit pour voir les nouvelles stratégies.")
