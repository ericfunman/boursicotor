#!/usr/bin/env python3
"""Module documentation."""

"""
Script de diagnostic IBKR/LYNX - Version ultra-simple
Évite tous les problèmes d'asyncio
"""

import sys
import os
import json
from datetime import datetime

# Ajouter le backend au chemin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("🔍 DIAGNOSTIC IBKR/LYNX - VERSION SIMPLE")
    print("=" * 60)
    
    print("\n📊 [1/5] Vérification de la configuration...")
    
    # Load config depuis .env
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv('IBKR_HOST', '127.0.0.1')
    port = int(os.getenv('IBKR_PORT', '4002'))
    account = os.getenv('IBKR_ACCOUNT', 'DU0118471')
    
    print(f"   ✅ Host: {host}")
    print(f"   ✅ Port: {port}")
    print(f"   ✅ Compte: {account}")
    
    print("\n🔌 [2/5] Vérification de la connexion socket...")
    
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ IB Gateway accessible sur {host}:{port}")
        else:
            print(f"   ❌ IB Gateway inaccessible sur {host}:{port}")
            print("   ⚠️ Le portail LYNX doit être lancé!")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    print("\n🔧 [3/5] Test des imports ib_insync...")
    
    try:
        # Test simple sans connexion
        from ib_insync import Stock
        print("   ✅ ib_insync importer avec succès")
    except Exception as e:
        print(f"   ❌ Erreur d'import: {e}")
        return False
    
    print("\n📡 [4/5] Test de connexion IBKR...")
    
    try:
        from ib_insync import IB
        
        # Créer une instance sans asyncio
        ib = IB()
        print("   ⏳ Connexion en cours (timeout: 5s)...")
        
        # Connexion synchrone
        ib.connect(host, port, clientId=999, timeout=5)
        
        if ib.isConnected():
            print("   ✅ Connecté à IBKR!")
            
            # Récupérer infos du compte
            try:
                accounts = ib.managedAccounts()
                print(f"   📊 Comptes gérés: {accounts}")
                
                # Récupérer le résumé du compte
                summary = ib.accountSummary()
                print(f"\n   📈 Résumé du compte:")
                
                shown_keys = set()
                for item in summary:
                    if item.tag in ['AccountType', 'NetLiquidation', 'TotalCashValue', 'AvailableFunds']:
                        if item.tag not in shown_keys:
                            print(f"      {item.tag}: {item.value}")
                            shown_keys.add(item.tag)
                
            except Exception as e:
                print(f"   ⚠️ Erreur lors de la récupération du résumé: {e}")
            
            # Test de qualification de symbole
            print(f"\n   🔍 Test de qualification de symboles:")
            
            test_symbols = [
                ('AAPL', 'USD'),
                ('TSLA', 'USD'),
                ('TTE', 'EUR'),
                ('WLN', 'EUR'),
            ]
            
            for symbol, currency in test_symbols:
                try:
                    contract = Stock(symbol, 'SMART', currency)
                    qualified = ib.qualifyContracts(contract)
                    
                    if qualified:
                        q = qualified[0]
                        print(f"      ✅ {symbol}: {q.exchange} ({q.currency})")
                    else:
                        print(f"      ❌ {symbol}: Non qualifié")
                except Exception as e:
                    print(f"      ❌ {symbol}: Erreur - {str(e)[:40]}")
            
            # Déconnecter proprement
            ib.disconnect()
            print("\n   ✅ Déconnecté proprement")
            
        else:
            print("   ❌ Impossible de se connecter")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n📋 [5/5] Génération du rapport...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': 'OK',
        'host': host,
        'port': port,
        'account': account,
        'message': 'Diagnostic terminé avec succès'
    }
    
    with open('ibkr_diagnostics.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("   ✅ Rapport sauvegardé: ibkr_diagnostics.json")
    
    print("\n" + "=" * 60)
    print("✅ DIAGNOSTIC TERMINÉ AVEC SUCCÈS")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Diagnostic interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur non gérée: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
