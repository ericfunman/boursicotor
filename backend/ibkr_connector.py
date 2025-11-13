"""
Module de connexion à Interactive Brokers via l'API TWS
Compatible avec Lynx (qui utilise la même API qu'IBKR)
"""

import time
import threading
from datetime import datetime
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
from backend.constants import MSG_IBKR_NOT_CONNECTED


class IBKRWrapper(EWrapper):
    """Classe pour recevoir les callbacks de l'API IBKR"""
    
    def __init__(self):
        """TODO: Add docstring."""
        EWrapper.__init__(self)
        self.next_order_id = None
        self.market_data = {}
        self.historical_data = {}
        self.contract_details_list = []
        self.data_ready = threading.Event()
        
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):  # noqa: S117
        """Gestion des erreurs"""
        # Codes 2104 et 2106 sont des messages info, pas des erreurs
        if errorCode in [2104, 2106, 2158]:
            print(f"INFO {errorCode}: {errorString}")
        else:
            print(f"ERREUR {errorCode} (reqId {reqId}): {errorString}")
    
    def nextValidId(self, orderId: int):  # noqa: S117
        """Reçoit le prochain ID d'ordre valide"""
        self.next_order_id = orderId
        print(f"Connexion réussie! Prochain order ID: {orderId}")
    
    def tickPrice(self, reqId, tickType, price, attrib):  # noqa: S117
        """Reçoit les prix en temps réel"""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        
        # TickType: 1=bid, 2=ask, 4=last, 6=high, 7=low, 9=close
        tick_names = {1: 'bid', 2: 'ask', 4: 'last', 6: 'high', 7: 'low', 9: 'close'}
        if tickType in tick_names:
            self.market_data[reqId][tick_names[tickType]] = price
            self.market_data[reqId]['timestamp'] = datetime.now()
    
    def tickSize(self, reqId, tickType, size):  # noqa: S117
        """Reçoit les volumes en temps réel"""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        
        # TickType: 0=bid_size, 3=ask_size, 5=last_size, 8=volume
        tick_names = {0: 'bid_size', 3: 'ask_size', 5: 'last_size', 8: 'volume'}
        if tickType in tick_names:
            self.market_data[reqId][tick_names[tickType]] = size
    
    def historicalData(self, reqId, bar):  # noqa: S117
        """Reçoit les données historiques"""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
    
    def historicalDataEnd(self, reqId, start, end):  # noqa: S117
        """Signale la fin de la réception des données historiques"""
        print(f"Données historiques reçues pour reqId {reqId}: {start} à {end}")
        self.data_ready.set()
    
    def contractDetails(self, reqId, contractDetails):
        """Reçoit les détails d'un contrat"""
        self.contract_details_list.append(contractDetails)
    
    def contractDetailsEnd(self, reqId):
        """Signale la fin de la réception des détails de contrat"""
        print(f"Détails du contrat reçus pour reqId {reqId}")
        self.data_ready.set()


class IBKRClient(EClient):
    """Classe client pour envoyer des requêtes à IBKR"""
    
    def __init__(self, wrapper):
        """TODO: Add docstring."""
        EClient.__init__(self, wrapper)


class IBKRConnector:
    """
    Connecteur principal pour IBKR/Lynx
    """
    
    def __init__(self, host='127.0.0.1', port=4002, client_id=1):
        """
        Initialise le connecteur IBKR/Lynx
        
        Args:
            host: Adresse IP du serveur TWS/IB Gateway (localhost par défaut)
            port: Port de connexion
                - 4001 pour IB Gateway Live (Lynx)
                - 4002 pour IB Gateway Paper/Demo (Lynx)
                - 7496 pour TWS Live
                - 7497 pour TWS Paper/Demo
            client_id: ID unique du client (0-32)
        """
        self.wrapper = IBKRWrapper()
        self.client = IBKRClient(self.wrapper)
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        self.thread = None
        
    def connect(self):
        """Établit la connexion avec TWS/IB Gateway"""
        try:
            self.client.connect(self.host, self.port, self.client_id)
            
            # Démarrer le thread pour gérer les messages
            self.thread = threading.Thread(target=self.client.run, daemon=True)
            self.thread.start()
            
            # Attendre la confirmation de connexion
            time.sleep(2)
            
            if self.client.isConnected():
                self.connected = True
                print(f"✅ Connecté à IBKR sur {self.host}:{self.port}")
                return True
            else:
                print("❌ Échec de la connexion à IBKR")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion IBKR: {e}")
            return False
    
    def disconnect(self):
        """Déconnecte de TWS/IB Gateway"""
        if self.connected:
            self.client.disconnect()
            self.connected = False
            print("🔌 Déconnecté de IBKR")
    
    def create_contract(self, symbol, sec_type='STK', exchange='SMART', currency='EUR'):
        """
        Crée un objet Contract pour IBKR
        
        Args:
            symbol: Symbole du ticker (ex: 'AIR' pour Airbus)
            sec_type: Type de sécurité ('STK'=action, 'FUT'=future, 'OPT'=option)
            exchange: Bourse ('SMART', 'EURONEXT', 'NYSE', etc.)
            currency: Devise ('EUR', 'USD', etc.)
        
        Returns:
            Contract object
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def get_market_data(self, contract, req_id=1):
        """
        Demande les données de marché en temps réel
        
        Args:
            contract: Objet Contract IBKR
            req_id: ID unique de la requête
        
        Returns:
            dict avec les données de marché ou None
        """
        if not self.connected:
            print(MSG_IBKR_NOT_CONNECTED)
            return None
        
        # Demander les données de marché
        self.client.reqMktData(req_id, contract, "", False, False, [])
        
        # Attendre que les données arrivent
        time.sleep(2)
        
        # Annuler la souscription
        self.client.cancelMktData(req_id)
        
        return self.wrapper.market_data.get(req_id)
    
    def get_historical_data(self, contract, duration='1 M', bar_size='1 day', 
                           what_to_show='TRADES', req_id=2):
        """
        Récupère les données historiques
        
        Args:
            contract: Objet Contract IBKR
            duration: Durée des données ('1 D', '1 W', '1 M', '1 Y')
            bar_size: Taille des barres ('1 min', '5 mins', '1 hour', '1 day')
            what_to_show: Type de données ('TRADES', 'MIDPOINT', 'BID', 'ASK')
            req_id: ID unique de la requête
        
        Returns:
            DataFrame avec les données historiques
        """
        if not self.connected:
            print(MSG_IBKR_NOT_CONNECTED)
            return None
        
        # Réinitialiser l'événement
        self.wrapper.data_ready.clear()
        self.wrapper.historical_data[req_id] = []
        
        # Demander les données historiques
        self.client.reqHistoricalData(
            reqId=req_id,
            contract=contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=1,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )
        
        # Attendre la réception des données (max 10 secondes)
        self.wrapper.data_ready.wait(timeout=10)
        
        # Convertir en DataFrame
        if req_id in self.wrapper.historical_data and self.wrapper.historical_data[req_id]:
            df = pd.DataFrame(self.wrapper.historical_data[req_id])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        else:
            print(f"⚠️ Aucune donnée historique reçue pour reqId {req_id}")
            return None
    
    def search_contract(self, symbol, sec_type='STK', req_id=3):
        """
        Recherche les détails d'un contrat
        
        Args:
            symbol: Symbole à rechercher
            sec_type: Type de sécurité
            req_id: ID unique de la requête
        
        Returns:
            Liste des ContractDetails trouvés
        """
        if not self.connected:
            print(MSG_IBKR_NOT_CONNECTED)
            return None
        
        # Réinitialiser
        self.wrapper.data_ready.clear()
        self.wrapper.contract_details_list = []
        
        # Créer un contrat de recherche
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = 'SMART'
        
        # Demander les détails
        self.client.reqContractDetails(req_id, contract)
        
        # Attendre la réponse
        self.wrapper.data_ready.wait(timeout=5)
        
        return self.wrapper.contract_details_list


# Fonction utilitaire pour tester la connexion
def test_connection():
    """Test de connexion à IBKR/Lynx"""
    print("🔌 Test de connexion à IBKR/Lynx...")
    print("\n⚠️  IMPORTANT: Avant de lancer ce test, assurez-vous que:")
    print("   1. TWS ou IB Gateway est lancé avec vos identifiants Lynx")
    print("   2. L'API est activée (Configure > API > Settings)")
    print("   3. Vous utilisez le bon port:")
    print("      - Port 4002 pour IB Gateway Demo/Paper")
    print("      - Port 4001 pour IB Gateway Live")
    print("      - Port 7497 pour TWS Demo/Paper")
    print("      - Port 7496 pour TWS Live\n")
    
    connector = IBKRConnector(
        host='127.0.0.1',
        port=4002,  # IB Gateway Paper Trading (Lynx Demo)
        client_id=1
    )
    
    if connector.connect():
        print("\n✅ Connexion établie!")
        
        # Test: Rechercher un contrat
        print("\n🔍 Recherche du contrat AIR (Airbus)...")
        details = connector.search_contract('AIR', 'STK')
        if details:
            print(f"   Trouvé {len(details)} contrat(s)")
            for detail in details[:3]:  # Afficher les 3 premiers
                print(f"   - {detail.contract.symbol} @ {detail.contract.exchange}")
        
        # Test: Données de marché
        print("\n📊 Récupération des données de marché pour AIR...")
        contract = connector.create_contract('AIR', 'STK', 'SMART', 'EUR')
        market_data = connector.get_market_data(contract)
        if market_data:
            print(f"   Prix: {market_data}")
        
        # Test: Données historiques
        print("\n📈 Récupération des données historiques...")
        hist_data = connector.get_historical_data(contract, duration='5 D', bar_size='1 day')
        if hist_data is not None:
            print(f"   {len(hist_data)} barres reçues")
            print(hist_data.tail())
        
        connector.disconnect()
    else:
        print("\n❌ Impossible de se connecter. Vérifiez que:")
        print("   1. TWS ou IB Gateway est lancé")
        print("   2. L'API est activée dans TWS (Config > API > Settings)")
        print("   3. Le port est correct (7497 pour paper, 7496 pour live)")


if __name__ == '__main__':
    test_connection()
