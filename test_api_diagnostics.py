#!/usr/bin/env python3
"""
Script de diagnostic complet des API IBKR/LYNX
Vérifie les permissions, souscriptions de données, et capacités d'accès
"""

import sys
import asyncio

# Fix pour Python 3.10+ sur Windows AVANT d'importer ib_insync
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from ib_insync import IB, Stock, Contract
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple

class IBKRDiagnostics:
    def __init__(self, host='127.0.0.1', port=7497, clientId=999):
        self.ib = IB()
        self.host = host
        self.port = port
        self.clientId = clientId
        self.connected = False
        self.results = {}
        
    def connect(self) -> bool:
        """Connexion à IB Gateway/TWS"""
        print("🔌 [1/8] Connexion à IB Gateway...")
        try:
            self.ib.connect(self.host, self.port, clientId=self.clientId)
            print("✅ Connexion établie")
            self.connected = True
            self.results['connection'] = {'status': 'OK'}
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            print("   Assurez-vous que IB Gateway est lancé sur 127.0.0.1:7497")
            self.results['connection'] = {'status': 'ERREUR', 'message': str(e)}
            return False
    
    def check_account_info(self) -> Dict:
        """Vérifie les infos du compte (simulé vs réel)"""
        print("\n📊 [2/8] Infos du compte...")
        try:
            # Récupérer l'identifiant du compte
            accounts = self.ib.managedAccounts()
            print(f"   Comptes gérés: {accounts}")
            
            # Récupérer le statut du compte
            account_summary = self.ib.accountSummary()
            
            account_type = None
            is_simulated = None
            
            for item in account_summary:
                if item.tag == 'AccountType':
                    account_type = item.value
                    print(f"   Type de compte: {account_type}")
                if item.tag == 'AccountCode':
                    print(f"   Code compte: {item.value}")
                    is_simulated = 'DU' in str(item.value).upper() or 'PAPER' in str(item.value).upper()
            
            self.results['account'] = {
                'status': 'OK',
                'accounts': list(accounts),
                'type': account_type,
                'is_simulated': is_simulated
            }
            
            if is_simulated or 'paper' in str(account_type).lower():
                print("   ⚙️ Mode SIMULÉ détecté")
            else:
                print("   ⚙️ Mode RÉEL ou INDÉTERMINÉ")
                
            return {'status': 'OK', 'accounts': accounts, 'type': account_type}
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.results['account'] = {'status': 'ERREUR', 'message': str(e)}
            return {'status': 'ERREUR', 'message': str(e)}
    
    def check_market_data_subscriptions(self) -> Dict:
        """Vérifie les souscriptions de données de marché"""
        print("\n📡 [3/8] Souscriptions de données de marché...")
        try:
            # Les données de souscription se trouvent dans accountSummary
            account_summary = self.ib.accountSummary()
            
            subscriptions = {}
            subscription_keys = [
                'MarketDataSubscriptions',
                'MarketDataType',
                'ActiveFXSubscriptions',
            ]
            
            for item in account_summary:
                if any(key in item.tag for key in subscription_keys):
                    subscriptions[item.tag] = item.value
                    print(f"   {item.tag}: {item.value}")
            
            if not subscriptions:
                print("   ℹ️ Pas d'info de souscription trouvée (normal pour compte simulé)")
                print("   Vous aurez accès aux données DIFFÉRÉES par défaut")
            
            self.results['subscriptions'] = {'status': 'OK', 'subscriptions': subscriptions}
            return {'status': 'OK', 'subscriptions': subscriptions}
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.results['subscriptions'] = {'status': 'ERREUR', 'message': str(e)}
            return {'status': 'ERREUR', 'message': str(e)}
    
    def test_contract_qualification(self, symbol: str, currency: str = 'USD', exchange: str = 'SMART') -> Tuple[bool, str]:
        """Teste si un contrat peut être qualifié"""
        try:
            contract = Stock(symbol, exchange, currency)
            qualified = self.ib.qualifyContracts(contract)
            
            if qualified:
                q = qualified[0]
                return True, f"{q.symbol}/{q.currency}@{q.exchange}"
            else:
                return False, "Non qualifié"
                
        except Exception as e:
            return False, str(e)
    
    def check_symbols(self) -> Dict:
        """Teste plusieurs symboles pour vérifier l'accès"""
        print("\n🔍 [4/8] Test de qualification de symboles...")
        
        test_symbols = [
            ('AAPL', 'USD', 'NASDAQ'),  # Tech US
            ('TSLA', 'USD', 'NASDAQ'),  # Tech US
            ('MSFT', 'USD', 'NASDAQ'),  # Tech US
            ('TTE', 'EUR', 'EURONEXT'),  # Euronext Paris
            ('WLN', 'EUR', 'WIENERBOERSE'),  # Vienne
            ('SAP', 'EUR', 'XETRA'),  # Deutsche Börse
        ]
        
        results = {}
        
        for symbol, currency, exchange in test_symbols:
            success, info = self.test_contract_qualification(symbol, currency, exchange)
            status = "✅" if success else "❌"
            print(f"   {status} {symbol:6} ({currency}/{exchange:12}): {info}")
            results[symbol] = {
                'success': success,
                'currency': currency,
                'exchange': exchange,
                'info': info
            }
        
        self.results['symbols'] = results
        return results
    
    def check_market_data_access(self, symbol: str = 'AAPL', currency: str = 'USD') -> Dict:
        """Teste l'accès aux données de marché en temps réel"""
        print(f"\n📈 [5/8] Accès aux données de marché ({symbol})...")
        
        try:
            contract = Stock(symbol, 'SMART', currency)
            qualified = self.ib.qualifyContracts(contract)
            
            if not qualified:
                print(f"   ❌ {symbol} ne peut pas être qualifié")
                return {'status': 'ERREUR', 'message': 'Non qualifié'}
            
            contract = qualified[0]
            
            # Demander les données de marché
            self.ib.reqMktData(contract, '', False, False)
            
            # Attendre un tick
            print("   ⏳ En attente de données...")
            ticks = self.ib.sleep(2)  # Attend 2 secondes
            
            # Récupérer les données
            ticker = self.ib.ticker(contract)
            
            result = {
                'status': 'OK',
                'symbol': symbol,
                'bid': ticker.bid,
                'ask': ticker.ask,
                'last': ticker.last,
                'volume': ticker.volume,
            }
            
            print(f"   ✅ Données reçues:")
            print(f"      Bid: {ticker.bid}")
            print(f"      Ask: {ticker.ask}")
            print(f"      Last: {ticker.last}")
            print(f"      Volume: {ticker.volume}")
            
            self.ib.cancelMktData(contract)
            self.results['market_data'] = result
            return result
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            self.results['market_data'] = {'status': 'ERREUR', 'message': str(e)}
            return {'status': 'ERREUR', 'message': str(e)}
    
    def check_historical_data(self, symbol: str = 'AAPL', currency: str = 'USD', days: int = 30) -> Dict:
        """Teste l'accès aux données historiques"""
        print(f"\n📊 [6/8] Données historiques ({symbol}, {days} jours)...")
        
        try:
            contract = Stock(symbol, 'SMART', currency)
            qualified = self.ib.qualifyContracts(contract)
            
            if not qualified:
                print(f"   ❌ {symbol} ne peut pas être qualifié")
                return {'status': 'ERREUR', 'message': 'Non qualifié'}
            
            contract = qualified[0]
            
            # Demander les données historiques
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=f'{days} D',
                barSizeSetting='1 day',
                whatToShow='MIDPOINT',  # MIDPOINT pour données différées
                useRTH=False,
                formatDate=1
            )
            
            if bars:
                print(f"   ✅ {len(bars)} barres reçues:")
                print(f"      Première: {bars[0].date} - Close: {bars[0].close}")
                print(f"      Dernière: {bars[-1].date} - Close: {bars[-1].close}")
                
                self.results['historical_data'] = {
                    'status': 'OK',
                    'symbol': symbol,
                    'bars_count': len(bars),
                    'first_date': str(bars[0].date),
                    'last_date': str(bars[-1].date),
                }
            else:
                print(f"   ⚠️ Aucune donnée historique")
                self.results['historical_data'] = {'status': 'AUCUNE_DONNEE'}
            
            return {'status': 'OK', 'bars': len(bars) if bars else 0}
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            self.results['historical_data'] = {'status': 'ERREUR', 'message': str(e)}
            return {'status': 'ERREUR', 'message': str(e)}
    
    def check_api_versions(self) -> Dict:
        """Vérifie les versions des composants"""
        print("\n🔧 [7/8] Versions des composants...")
        
        try:
            server_version = self.ib.serverVersion()
            client_version = self.ib.client.version
            
            print(f"   IB Gateway/TWS: v{server_version}")
            print(f"   Client (ib_insync): v{client_version}")
            
            self.results['versions'] = {
                'server': server_version,
                'client': client_version
            }
            
            return {'server': server_version, 'client': client_version}
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            self.results['versions'] = {'status': 'ERREUR', 'message': str(e)}
            return {}
    
    def generate_report(self) -> str:
        """Génère un rapport JSON"""
        print("\n📋 [8/8] Génération du rapport...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results
        }
        
        # Sauvegarder le rapport
        report_file = 'ibkr_diagnostics_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"   ✅ Rapport sauvegardé dans {report_file}")
        
        return report_file
    
    def run_full_diagnostics(self):
        """Lance tous les diagnostics"""
        print("=" * 60)
        print("🔍 DIAGNOSTIC COMPLET DES API IBKR/LYNX")
        print("=" * 60)
        
        if not self.connect():
            print("\n❌ Impossible de continuer sans connexion")
            return False
        
        try:
            # Exécuter tous les tests
            self.check_account_info()
            self.check_market_data_subscriptions()
            self.check_symbols()
            self.check_market_data_access('AAPL', 'USD')
            self.check_historical_data('AAPL', 'USD', 30)
            self.check_api_versions()
            
            # Rapport
            report_file = self.generate_report()
            
            print("\n" + "=" * 60)
            print("📊 RÉSUMÉ")
            print("=" * 60)
            
            # Analyser les résultats
            self._print_summary()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erreur générale: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.connected:
                self.ib.disconnect()
                print("\n🔌 Déconnecté")
    
    def _print_summary(self):
        """Affiche un résumé des résultats"""
        
        # Compte
        account = self.results.get('account', {})
        if account.get('status') == 'OK':
            print(f"✅ Compte: {account.get('accounts', ['?'])[0]}")
        else:
            print(f"❌ Compte: Erreur")
        
        # Symboles accessibles
        symbols = self.results.get('symbols', {})
        accessible = [s for s, info in symbols.items() if info.get('success')]
        if accessible:
            print(f"✅ Symboles accessibles ({len(accessible)}): {', '.join(accessible)}")
        
        # Données de marché
        md = self.results.get('market_data', {})
        if md.get('status') == 'OK':
            print(f"✅ Données de marché: Accessibles (Bid/Ask disponibles)")
        else:
            print(f"⚠️ Données de marché: Non testées ou erreur")
        
        # Données historiques
        hist = self.results.get('historical_data', {})
        if hist.get('status') == 'OK':
            print(f"✅ Données historiques: {hist.get('bars_count', '?')} barres")
        else:
            print(f"⚠️ Données historiques: Non accessibles")
        
        print("\n💡 Recommandations:")
        print("   1. Si AAPL/TSLA OK mais TTE/WLN ❌:")
        print("      → Souscription manquante pour Euronext/Wienerböse")
        print("   2. Si Bid/Ask vides:")
        print("      → Données DIFFÉRÉES (normal en simulé)")
        print("   3. Si aucun symbole accessible:")
        print("      → Vérifier les paramètres API dans LYNX/IB Gateway")


if __name__ == '__main__':
    diag = IBKRDiagnostics(host='127.0.0.1', port=7497, clientId=999)
    success = diag.run_full_diagnostics()
    sys.exit(0 if success else 1)
