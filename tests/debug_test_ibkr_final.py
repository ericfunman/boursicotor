#!/usr/bin/env python3
"""Module documentation."""

"""
Test direct avec gestion de l'event loop
"""

import sys
import os

# SOLUTION: Créer l'event loop AVANT les imports
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
else:
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

# Maintenant importer ib_insync
from ib_insync import IB, Stock
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

print("=" * 60)
print("🔍 TEST DIRECT IBKR/LYNX")
print("=" * 60)

host = os.getenv('IBKR_HOST', '127.0.0.1')
port = int(os.getenv('IBKR_PORT', '4002'))
account = os.getenv('IBKR_ACCOUNT', 'DU0118471')

print(f"\n📊 Configuration:")
print(f"   Host: {host}")
print(f"   Port: {port}")
print(f"   Compte: {account}")

print(f"\n🔌 Connexion...")

try:
    ib = IB()
    ib.connect(host, port, clientId=999, timeout=5)
    
    if not ib.isConnected():
        print("❌ Connexion échouée")
        sys.exit(1)
    
    print("✅ Connecté!")
    
    # Infos du compte
    print(f"\n📊 Infos du compte:")
    accounts = ib.managedAccounts()
    print(f"   Comptes: {accounts}")
    
    # Test de symboles
    print(f"\n🔍 Test de symboles:")
    
    symbols = [
        ('AAPL', 'USD', 'NASDAQ'),
        ('TSLA', 'USD', 'NASDAQ'),
        ('TTE', 'EUR', 'EURONEXT'),
        ('WLN', 'EUR', 'WIENERBOERSE'),
        ('MSFT', 'USD', 'NASDAQ'),
    ]
    
    results = {}
    for symbol, currency, expected_exchange in symbols:
        try:
            contract = Stock(symbol, 'SMART', currency)
            qualified = ib.qualifyContracts(contract)
            
            if qualified:
                q = qualified[0]
                status = f"✅ {q.exchange} ({q.currency})"
                results[symbol] = {'status': 'OK', 'exchange': q.exchange, 'currency': q.currency}
            else:
                status = f"❌ Non qualifié"
                results[symbol] = {'status': 'FAIL', 'reason': 'Non qualifié'}
        except Exception as e:
            status = f"❌ Erreur: {str(e)[:30]}"
            results[symbol] = {'status': 'ERROR', 'error': str(e)[:50]}
        
        print(f"   {symbol:6} {status}")
    
    # Résumé
    print(f"\n📈 Résumé:")
    ok_count = sum(1 for r in results.values() if r['status'] == 'OK')
    fail_count = sum(1 for r in results.values() if r['status'] != 'OK')
    print(f"   ✅ Symboles accessibles: {ok_count}/{len(symbols)}")
    print(f"   ❌ Symboles inaccessibles: {fail_count}/{len(symbols)}")
    
    # Sauvegarder
    report = {
        'timestamp': datetime.now().isoformat(),
        'connected': True,
        'account': account,
        'symbols_tested': len(symbols),
        'symbols_ok': ok_count,
        'symbols': results
    }
    
    with open('ibkr_test_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Rapport: ibkr_test_results.json")
    
    ib.disconnect()
    print("✅ Déconnecté")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TEST TERMINÉ")
print("=" * 60)
