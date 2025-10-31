"""
Script pour créer une stratégie d'exemple dans la base de données
"""

from backend.models import SessionLocal, Strategy
import json

def create_example_strategy():
    """Crée une stratégie RSI + MACD d'exemple"""
    db = SessionLocal()
    
    try:
        # Vérifier si la stratégie existe déjà
        existing = db.query(Strategy).filter(Strategy.name == "RSI + MACD Momentum").first()
        
        if existing:
            print("✅ La stratégie 'RSI + MACD Momentum' existe déjà")
            return
        
        # Paramètres de la stratégie
        # Conditions simples: Achat quand RSI < 30 et MACD > Signal
        #                    Vente quand RSI > 70 et MACD < Signal
        parameters = {
            "buy_conditions": "rsi is not None and macd is not None and macd_signal is not None and rsi < 30 and macd > macd_signal",
            "sell_conditions": "rsi is not None and macd is not None and macd_signal is not None and rsi > 70 and macd < macd_signal",
            "indicators": ["RSI_14", "MACD"],
            "description": "Achat lorsque RSI < 30 (survendu) ET MACD croise au-dessus du signal. Vente lorsque RSI > 70 (suracheté) ET MACD croise en-dessous du signal."
        }
        
        # Créer la stratégie
        strategy = Strategy(
            name="RSI + MACD Momentum",
            description="Stratégie de momentum basée sur RSI et MACD. Capture les retournements de tendance en zone de surachat/survente.",
            strategy_type="momentum",
            parameters=json.dumps(parameters),
            is_active=True
        )
        
        db.add(strategy)
        db.commit()
        
        print("✅ Stratégie 'RSI + MACD Momentum' créée avec succès!")
        print(f"   - Type: {strategy.strategy_type}")
        print(f"   - Conditions d'achat: RSI < 30 ET MACD > Signal")
        print(f"   - Conditions de vente: RSI > 70 ET MACD < Signal")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la stratégie: {e}")
        db.rollback()
    finally:
        db.close()


def create_aggressive_strategy():
    """Crée une stratégie plus aggressive"""
    db = SessionLocal()
    
    try:
        # Vérifier si la stratégie existe déjà
        existing = db.query(Strategy).filter(Strategy.name == "RSI Aggressive").first()
        
        if existing:
            print("✅ La stratégie 'RSI Aggressive' existe déjà")
            return
        
        # Paramètres de la stratégie plus aggressive
        parameters = {
            "buy_conditions": "rsi is not None and rsi < 35",
            "sell_conditions": "rsi is not None and rsi > 65",
            "indicators": ["RSI_14"],
            "description": "Achat agressif dès que RSI < 35, Vente dès que RSI > 65"
        }
        
        # Créer la stratégie
        strategy = Strategy(
            name="RSI Aggressive",
            description="Stratégie aggressive basée uniquement sur RSI avec seuils élargis",
            strategy_type="mean_reversion",
            parameters=json.dumps(parameters),
            is_active=True
        )
        
        db.add(strategy)
        db.commit()
        
        print("✅ Stratégie 'RSI Aggressive' créée avec succès!")
        print(f"   - Type: {strategy.strategy_type}")
        print(f"   - Conditions d'achat: RSI < 35")
        print(f"   - Conditions de vente: RSI > 65")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la stratégie: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🎯 Création de stratégies d'exemple...\n")
    create_example_strategy()
    print()
    create_aggressive_strategy()
    print("\n✅ Terminé! Vous pouvez maintenant tester ces stratégies dans la page 'Cours Live'.")
