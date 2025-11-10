"""
Test Interactive Brokers / Lynx connection
"""
import sys
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from backend.config import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🧪 Test de connexion IBKR / Lynx")
print("=" * 60)
print()

# Display configuration
IBKR_HOST = os.getenv('IBKR_HOST', '127.0.0.1')
IBKR_PORT = int(os.getenv('IBKR_PORT', '7497'))
IBKR_CLIENT_ID = int(os.getenv('IBKR_CLIENT_ID', '1'))
IBKR_ACCOUNT = os.getenv('IBKR_ACCOUNT', 'DU0118471')

print(f"📋 Configuration:")
print(f"   Host: {IBKR_HOST}")
print(f"   Port: {IBKR_PORT}")
print(f"   Client ID: {IBKR_CLIENT_ID}")
print(f"   Account: {IBKR_ACCOUNT}")
print()

# Check if ib_insync is installed
try:
    from ib_insync import IB, Stock, util
    print("✅ Bibliothèque ib_insync installée")
except ImportError:
    print("❌ Bibliothèque ib_insync non installée")
    print()
    print("Installation requise:")
    print("   pip install ib_insync")
    sys.exit(1)

print()
print("-" * 60)
print("🔌 Tentative de connexion à IB Gateway...")
print("-" * 60)
print()

try:
    # Create IB instance
    ib = IB()
    
    # Connect to IB Gateway
    print(f"⏳ Connexion à {IBKR_HOST}:{IBKR_PORT}...")
    ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
    
    print("✅ Connexion établie avec succès!")
    print()
    
    # Get account information
    print("-" * 60)
    print("📊 Informations du compte")
    print("-" * 60)
    print()
    
    # Get managed accounts
    accounts = ib.managedAccounts()
    print(f"📋 Comptes gérés: {', '.join(accounts)}")
    print()
    
    # Use accountSummary() - more reliable and faster
    print("⏳ Récupération du résumé du compte...")
    
    summary_tags = [
        'AccountType', 'NetLiquidation', 'TotalCashValue', 
        'BuyingPower', 'AvailableFunds', 'GrossPositionValue',
        'UnrealizedPnL', 'RealizedPnL', 'EquityWithLoanValue',
        'InitMarginReq', 'MaintMarginReq'
    ]
    
    # Request account summary for all accounts
    account_summary = ib.accountSummary()
    ib.sleep(2)  # Wait for data to arrive
    
    if account_summary:
        print(f"✅ {len(account_summary)} valeurs reçues")
        print()
        
        # Group by currency
        summary_by_currency = {}
        for item in account_summary:
            if item.currency not in summary_by_currency:
                summary_by_currency[item.currency] = {}
            summary_by_currency[item.currency][item.tag] = item.value
        
        # Display by currency
        tag_labels = {
            'AccountType': 'Type de compte',
            'NetLiquidation': '💰 Valeur nette totale',
            'TotalCashValue': 'Cash total',
            'BuyingPower': 'Pouvoir d\'achat',
            'AvailableFunds': 'Fonds disponibles',
            'GrossPositionValue': 'Valeur positions',
            'UnrealizedPnL': 'P&L non réalisé',
            'RealizedPnL': 'P&L réalisé',
            'EquityWithLoanValue': 'Capital avec prêt',
            'InitMarginReq': 'Marge initiale',
            'MaintMarginReq': 'Marge maintenance'
        }
        
        for currency, values in summary_by_currency.items():
            if currency:  # Skip empty/base currency entries
                print(f"   💵 Devise: {currency}")
                print(f"   {'-' * 70}")
                for tag in summary_tags:
                    if tag in values:
                        label = tag_labels.get(tag, tag)
                        value_str = values[tag]
                        try:
                            value_float = float(value_str)
                            if abs(value_float) >= 1000:
                                print(f"   {label:30} : {value_float:>25,.2f} {currency}")
                            else:
                                print(f"   {label:30} : {value_float:>25.2f} {currency}")
                        except:
                            print(f"   {label:30} : {value_str:>25} {currency}")
                print()
    else:
        print("⚠️ Aucune donnée de compte reçue")
    
    print()
    
    # Get positions
    print("-" * 60)
    print("📈 Positions actuelles")
    print("-" * 60)
    print()
    
    positions = ib.positions(IBKR_ACCOUNT)
    
    if positions:
        for pos in positions:
            print(f"   {pos.contract.symbol:10} : {pos.position:>8} @ {pos.avgCost:.2f}")
    else:
        print("   Aucune position ouverte")
    
    print()
    
    # Test market data subscription for a French stock
    print("-" * 60)
    print("📡 Test de données de marché (WLN - Worldline)")
    print("-" * 60)
    print()
    
    # Create contract for Worldline (Euronext Paris)
    wln_contract = Stock('WLN', 'SMART', 'EUR')
    
    print("⏳ Qualification du contrat...")
    contracts = ib.qualifyContracts(wln_contract)
    
    if contracts:
        contract = contracts[0]
        print(f"✅ Contrat qualifié: {contract.symbol} ({contract.primaryExchange})")
        print()
        
        # Request market data
        print("⏳ Demande de données de marché...")
        ticker = ib.reqMktData(contract)
        
        # Wait for data
        ib.sleep(2)
        
        if ticker.last > 0 or ticker.bid > 0 or ticker.ask > 0:
            print("✅ Données de marché reçues:")
            print(f"   Dernier prix : {ticker.last if ticker.last > 0 else 'N/A'}")
            print(f"   Bid         : {ticker.bid if ticker.bid > 0 else 'N/A'}")
            print(f"   Ask         : {ticker.ask if ticker.ask > 0 else 'N/A'}")
            print(f"   Volume      : {ticker.volume if ticker.volume > 0 else 'N/A'}")
            print(f"   Heure       : {ticker.time}")
        else:
            print("⚠️  Pas de données temps réel (marché fermé ou données différées)")
        
        # Cancel market data
        ib.cancelMktData(contract)
    else:
        print("❌ Impossible de qualifier le contrat WLN")
    
    print()
    
    # Test historical data
    print("-" * 60)
    print("📜 Test de données historiques (WLN - 1 jour)")
    print("-" * 60)
    print()
    
    if contracts:
        contract = contracts[0]
        
        print("⏳ Demande de données historiques...")
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='1 min',
            whatToShow='TRADES',
            useRTH=False,
            formatDate=1
        )
        
        if bars:
            print(f"✅ {len(bars)} barres reçues")
            print()
            print("   Dernières barres:")
            for bar in bars[-5:]:
                print(f"   {bar.date} | O:{bar.open:.2f} H:{bar.high:.2f} L:{bar.low:.2f} C:{bar.close:.2f} V:{bar.volume}")
        else:
            print("⚠️  Aucune donnée historique disponible")
    
    print()
    
    # Disconnect
    print("-" * 60)
    print("🔌 Déconnexion...")
    print("-" * 60)
    print()
    
    ib.disconnect()
    print("✅ Déconnecté avec succès")
    
    print()
    print("=" * 60)
    print("✅ Test réussi ! Votre connexion IBKR/Lynx fonctionne")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    print("Vérifications:")
    print("1. IB Gateway est-il démarré?")
    print("2. L'API est-elle activée dans Configuration → API → Settings?")
    print("3. Le port 7497 est-il correct?")
    print("4. 127.0.0.1 est-il dans les IPs de confiance?")
    print()
    import traceback
    print("Détails de l'erreur:")
    print(traceback.format_exc())
    sys.exit(1)

finally:
    if 'ib' in locals() and ib.isConnected():
        ib.disconnect()
