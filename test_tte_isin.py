#!/usr/bin/env python3
"""
Test TTE collection avec ISIN
"""

import sys
import os
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from ib_insync import IB, Stock, Contract
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

print("=" * 60)
print("🔍 TEST TTE avec ISIN (FR0000120271)")
print("=" * 60)

host = os.getenv('IBKR_HOST', '127.0.0.1')
port = int(os.getenv('IBKR_PORT', '4002'))

print(f"\n📊 Configuration:")
print(f"   Host: {host}")
print(f"   Port: {port}")

print(f"\n🔌 Connexion...")

try:
    ib = IB()
    ib.connect(host, port, clientId=999, timeout=20)
    
    if not ib.isConnected():
        print("❌ Connexion échouée")
        sys.exit(1)
    
    print("✅ Connecté!")
    
    # Test 1: Via ISIN
    print(f"\n📍 Test 1: Qualification via ISIN")
    try:
        contract = Contract(secType='STK', isin='FR0000120271')
        qualified = ib.qualifyContracts(contract)
        
        if qualified:
            q = qualified[0]
            print(f"   ✅ ISIN FR0000120271 → {q.symbol} on {q.exchange} ({q.currency})")
        else:
            print(f"   ❌ ISIN non qualifié")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Via symbol TTE/EUR/SBF
    print(f"\n📍 Test 2: Qualification via symbol (TTE/EUR/SBF)")
    try:
        contract = Stock('TTE', 'SBF', 'EUR')
        qualified = ib.qualifyContracts(contract)
        
        if qualified:
            q = qualified[0]
            print(f"   ✅ TTE/SBF/EUR → {q.symbol} on {q.exchange} ({q.currency})")
        else:
            print(f"   ❌ Symbol non qualifié")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Via symbol TTE/SMART/USD (l'ancien qui timeout)
    print(f"\n📍 Test 3: Qualification via symbol (TTE/SMART/USD) - l'ancien")
    try:
        contract = Stock('TTE', 'SMART', 'USD')
        qualified = ib.qualifyContracts(contract)
        
        if qualified:
            q = qualified[0]
            print(f"   ✅ TTE/SMART/USD → {q.symbol} on {q.exchange} ({q.currency})")
        else:
            print(f"   ❌ Symbol non qualifié")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    ib.disconnect()
    print("\n✅ Déconnecté")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TEST TERMINÉ")
print("=" * 60)
