#!/usr/bin/env python3
"""
Script de diagnostic simplifié des API IBKR/LYNX
Évite les problèmes d'event loop
"""

import sys
import socket
import json
from datetime import datetime

def test_gateway_connection(host='127.0.0.1', port=4002):
    """Teste simplement la connexion au socket"""
    print(f"🔌 [1/3] Test de connexion à IB Gateway (port {port})...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ IB Gateway est accessible sur {host}:{port}")
            return True
        else:
            print(f"❌ IB Gateway n'est pas accessible sur {host}:{port}")
            print("   Assurez-vous que le portail LYNX est lancé et que IB Gateway est activé!")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_with_ib_insync():
    """Teste avec ib_insync en gérant l'event loop proprement"""
    print("\n📡 [2/3] Test avec ib_insync (API complète)...")
    
    try:
        # Importer APRÈS avoir créé l'event loop
        import asyncio
        
        async def run_tests():
            from ib_insync import IB, Stock
            
            ib = IB()
            
            try:
                print("   Connexion en cours...")
                ib.connect('127.0.0.1', 4002, clientId=999)
                print("   ✅ Connecté")
                
                # Test 1: Infos du compte
                print("\n   📊 Infos du compte:")
                accounts = ib.managedAccounts()
                print(f"      Comptes: {accounts}")
                
                # Test 2: Account summary
                print("\n   📈 Résumé du compte:")
                summary = ib.accountSummary()
                
                for item in summary:
                    if 'Type' in item.tag or 'Code' in item.tag or 'Currency' in item.tag:
                        print(f"      {item.tag}: {item.value}")
                
                # Test 3: Test de qualification de contrat
                print("\n   🔍 Test de qualification de symboles:")
                
                test_symbols = [
                    ('AAPL', 'USD', 'NASDAQ'),
                    ('TSLA', 'USD', 'NASDAQ'),
                    ('TTE', 'EUR', 'EURONEXT'),
                    ('WLN', 'EUR', 'WIENERBOERSE'),
                ]
                
                for symbol, currency, exchange in test_symbols:
                    try:
                        contract = Stock(symbol, 'SMART', currency)
                        qualified = ib.qualifyContracts(contract)
                        
                        if qualified:
                            q = qualified[0]
                            print(f"      ✅ {symbol}: {q.exchange} ({q.currency})")
                        else:
                            print(f"      ❌ {symbol}: Non qualifié")
                    except Exception as e:
                        print(f"      ❌ {symbol}: {str(e)[:50]}")
                
                # Test 4: Données de marché
                print("\n   📊 Test de données de marché (AAPL):")
                try:
                    contract = Stock('AAPL', 'SMART', 'USD')
                    qualified = ib.qualifyContracts(contract)
                    
                    if qualified:
                        contract = qualified[0]
                        ib.reqMktData(contract, '', False, False)
                        ib.sleep(2)
                        
                        ticker = ib.ticker(contract)
                        print(f"      ✅ Bid: {ticker.bid}, Ask: {ticker.ask}")
                        
                        ib.cancelMktData(contract)
                    else:
                        print(f"      ❌ AAPL non qualifié")
                
                except Exception as e:
                    print(f"      ⚠️ Erreur: {str(e)[:50]}")
                
                # Test 5: Données historiques
                print("\n   📈 Test de données historiques (AAPL, 5 jours):")
                try:
                    contract = Stock('AAPL', 'SMART', 'USD')
                    qualified = ib.qualifyContracts(contract)
                    
                    if qualified:
                        contract = qualified[0]
                        bars = ib.reqHistoricalData(
                            contract,
                            endDateTime='',
                            durationStr='5 D',
                            barSizeSetting='1 day',
                            whatToShow='MIDPOINT',
                            useRTH=False,
                            formatDate=1
                        )
                        
                        if bars:
                            print(f"      ✅ {len(bars)} barres reçues")
                            print(f"         Première: {bars[0].date}")
                            print(f"         Dernière: {bars[-1].date}")
                        else:
                            print(f"      ❌ Aucune donnée")
                
                except Exception as e:
                    print(f"      ⚠️ Erreur: {str(e)[:50]}")
                
                return True
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                return False
            finally:
                try:
                    ib.disconnect()
                except:
                    pass
        
        # Exécuter
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_tests())
        loop.close()
        
        return result
        
    except ImportError:
        print("   ❌ ib_insync non disponible")
        return False
    except Exception as e:
        print(f"   ❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_report():
    """Génère un rapport simple"""
    print("\n📋 [3/3] Génération du rapport...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'Diagnostic complété'
    }
    
    report_file = 'ibkr_diagnostics_simple.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"   ✅ Rapport sauvegardé dans {report_file}")

def main():
    print("=" * 60)
    print("🔍 DIAGNOSTIC SIMPLIFIÉ DES API IBKR/LYNX")
    print("=" * 60)
    
    # Test 1: Connexion socket
    if not test_gateway_connection():
        print("\n❌ IB Gateway n'est pas lancé!")
        print("   Lancez IB Gateway et relancez le script.")
        return False
    
    # Test 2: Tests API complets
    result = test_with_ib_insync()
    
    # Rapport
    generate_report()
    
    print("\n" + "=" * 60)
    print("✅ Diagnostic terminé")
    print("=" * 60)
    
    return result

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
