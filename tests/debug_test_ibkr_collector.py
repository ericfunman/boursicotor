"""
Test IBKR Data Collector
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.ibkr_collector import IBKRCollector

print("=" * 70)
print("🧪 Test du collecteur IBKR")
print("=" * 70)
print()

# Create collector
print("📡 Création du collecteur IBKR...")
collector = IBKRCollector()
print(f"✅ Collecteur créé: {collector.host}:{collector.port}")
print()

# Test connection
print("-" * 70)
print("🔌 Test de connexion...")
print("-" * 70)
print()

if collector.connect():
    print("✅ Connexion réussie!")
    print()
    
    # Test getting account summary
    print("-" * 70)
    print("💰 Récupération du résumé du compte...")
    print("-" * 70)
    print()
    
    account_summary = collector.get_account_summary()
    if account_summary:
        for currency, values in account_summary.items():
            if currency and currency != 'BASE':
                print(f"   💵 {currency}:")
                if 'NetLiquidation' in values:
                    net_liq = float(values['NetLiquidation'])
                    print(f"      Valeur nette: {net_liq:,.2f} {currency}")
                if 'BuyingPower' in values:
                    buying_power = float(values['BuyingPower'])
                    print(f"      Pouvoir d'achat: {buying_power:,.2f} {currency}")
        print()
    
    # Test getting positions
    print("-" * 70)
    print("📊 Récupération des positions...")
    print("-" * 70)
    print()
    
    positions = collector.get_positions()
    if positions:
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['position']} @ {pos['avg_cost']:.2f} {pos['currency']}")
    else:
        print("   Aucune position ouverte")
    print()
    
    # Test historical data collection
    print("-" * 70)
    print("📜 Test de collecte de données historiques (WLN - 1 semaine)")
    print("-" * 70)
    print()
    
    result = collector.collect_and_save(
        symbol='WLN',
        duration='1 W',
        bar_size='1 min',
        interval='1min',
        name='Worldline'
    )
    
    if result['success']:
        print(f"✅ Collecte réussie!")
        print(f"   Symbole: {result['symbol']}")
        print(f"   Nouveaux enregistrements: {result['new_records']}")
        print(f"   Enregistrements mis à jour: {result['updated_records']}")
        print(f"   Total: {result['total_records']}")
        print(f"   Intervalle: {result['interval']}")
        print(f"   Période: {result['date_range']}")
    else:
        print(f"❌ Erreur: {result.get('error', 'Unknown error')}")
    
    print()
    
    # Disconnect
    print("-" * 70)
    print("🔌 Déconnexion...")
    print("-" * 70)
    print()
    
    collector.disconnect()
    print("✅ Déconnecté")
    
else:
    print("❌ Échec de la connexion")
    print()
    print("Vérifications:")
    print("1. IB Gateway est-il démarré?")
    print("2. L'API est-elle activée?")
    print("3. Le port est-il correct (4002)?")

print()
print("=" * 70)
print("✅ Test terminé")
print("=" * 70)
