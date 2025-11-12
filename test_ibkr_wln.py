#!/usr/bin/env python3
"""
Script de test simple pour IBKR - Test récupération contrat WLN
"""
import sys
import os
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(message)s')

# Ajouter le répertoire backend au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from ibkr_collector import IBKRCollector
    from ib_insync import Stock, util
    print("✅ Imports réussis")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

def test_ibkr_connection():
    """Test de base de la connexion IBKR"""
    print("\n🔍 Test de connexion IBKR...")

    collector = IBKRCollector(client_id=2)  # Client ID différent pour éviter les conflits

    if not collector.connect():
        print("❌ Échec de connexion à IBKR")
        return False

    print("✅ Connecté à IBKR")
    return collector

def test_contract_by_isin(collector, isin, currency='EUR'):
    """Test de récupération de contrat par ISIN"""
    print(f"\n🔍 Test contrat par ISIN {isin} ({currency})")

    try:
        # Créer un contrat avec ISIN
        contract = Stock()
        contract.secIdType = 'ISIN'
        contract.secId = isin
        contract.currency = currency
        contract.exchange = 'SMART'  # Ou 'PAR' pour Euronext

        print(f"Contract ISIN créé: {contract}")

        # Test qualifyContracts avec timeout
        print("Appel qualifyContracts...")
        start_time = time.time()

        try:
            contracts = collector.ib.qualifyContracts(contract)
            elapsed = time.time() - start_time
            print(f"✅ qualifyContracts réussi en {elapsed:.2f}s")
            print(f"Résultats: {len(contracts) if contracts else 0} contrats")

            if contracts:
                qualified = contracts[0]
                print(f"Contrat qualifié: {qualified.symbol} ({qualified.secId}) on {qualified.primaryExchange}")
                return qualified

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ qualifyContracts échoué après {elapsed:.2f}s: {e}")

        # Test reqContractDetails
        print("Test reqContractDetails...")
        try:
            details = collector.ib.reqContractDetails(contract)
            print(f"reqContractDetails: {len(details) if details else 0} résultats")

            if details:
                qualified = details[0].contract
                print(f"✅ Contrat trouvé: {qualified.symbol} ({qualified.secId}) on {qualified.exchange}")
                return qualified

        except Exception as e:
            print(f"❌ reqContractDetails échoué: {e}")

    except Exception as e:
        print(f"❌ Erreur générale: {e}")

    return None

def test_contract_by_symbol(collector, symbol, exchange, currency):
    """Test de récupération de contrat par symbole et exchange"""
    print(f"\n🔍 Test contrat par symbole {symbol} sur {exchange} ({currency})")

    try:
        # Créer un contrat avec symbole
        contract = Stock(symbol, exchange, currency)

        print(f"Contract symbole créé: {contract}")

        # Test qualifyContracts avec timeout
        print("Appel qualifyContracts...")
        start_time = time.time()

        try:
            contracts = collector.ib.qualifyContracts(contract)
            elapsed = time.time() - start_time
            print(f"✅ qualifyContracts réussi en {elapsed:.2f}s")
            print(f"Résultats: {len(contracts) if contracts else 0} contrats")

            if contracts:
                qualified = contracts[0]
                print(f"Contrat qualifié: {qualified.symbol} on {qualified.primaryExchange}")
                return qualified

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ qualifyContracts échoué après {elapsed:.2f}s: {e}")

        # Test reqContractDetails
        print("Test reqContractDetails...")
        try:
            details = collector.ib.reqContractDetails(contract)
            print(f"reqContractDetails: {len(details) if details else 0} résultats")

            if details:
                qualified = details[0].contract
                print(f"✅ Contrat trouvé: {qualified.symbol} on {qualified.exchange}")
                return qualified

        except Exception as e:
            print(f"❌ reqContractDetails échoué: {e}")

    except Exception as e:
        print(f"❌ Erreur générale: {e}")

    return None

def test_market_data(collector, contract):
    """Test de récupération de données de marché"""
    print(f"\n🔍 Test données de marché pour {contract.symbol}")

    try:
        print("Demande de données de marché...")
        print(f"Contrat utilisé: {contract}")
        print(f"Exchange: {contract.exchange}, Primary: {contract.primaryExchange}")

        # Essayer d'abord avec l'exchange primaire (SBF)
        test_contract = contract
        if contract.primaryExchange and contract.primaryExchange != contract.exchange:
            print(f"Test avec exchange primaire: {contract.primaryExchange}")
            test_contract = Stock(contract.symbol, contract.primaryExchange, contract.currency)

        ticker = collector.ib.reqMktData(test_contract, '', False, False)

        # Attendre un peu pour les données
        print("Attente des données (5 secondes)...")
        time.sleep(5)

        print(f"Données reçues - Last: {ticker.last}, Open: {ticker.open}, Volume: {ticker.volume}")
        print(f"High: {ticker.high}, Low: {ticker.low}, Close: {ticker.close}")

        # Vérifier si on a des données valides
        has_data = False
        if ticker.last is not None and not (isinstance(ticker.last, float) and ticker.last != ticker.last):  # NaN check
            has_data = True
            print(f"✅ Données LAST valides: {ticker.last}")
        else:
            print("❌ Pas de données LAST valides")

        if has_data:
            print("✅ Données de marché reçues avec succès")
            return True
        else:
            print("❌ Pas de données de marché valides")

        # Annuler l'abonnement
        collector.ib.cancelMktData(test_contract)

    except Exception as e:
        print(f"❌ Erreur données de marché: {e}")

    return False

def main():
    print("🚀 Test IBKR - Récupération WLN (Worldline)")
    print("=" * 50)

    # Test connexion
    collector = test_ibkr_connection()
    if not collector:
        print("❌ Impossible de se connecter à IBKR")
        return

    # ISIN de WLN (Worldline)
    wln_isin = 'FR0011981968'

    # Test par ISIN
    contract = test_contract_by_isin(collector, wln_isin)

    if not contract:
        print("\n❌ ISIN échoué, test par symbole WLN...")
        # Fallback: test par symbole
        contract = test_contract_by_symbol(collector, 'WLN', 'SMART', 'EUR')

    if contract:
        print(f"\n🎯 Contrat WLN trouvé: {contract}")
        test_market_data(collector, contract)
    else:
        print("\n❌ Impossible de trouver le contrat WLN")

    # Déconnexion
    print("\n🔌 Déconnexion...")
    collector.disconnect()
    print("✅ Test terminé")

if __name__ == "__main__":
    main()