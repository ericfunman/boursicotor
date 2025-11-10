"""
Test de récupération de données historiques depuis Saxo Bank
"""
from brokers.saxo_client import SaxoClient
from backend.config import logger
import pandas as pd

def test_historical_data():
    """Test la récupération de données historiques"""
    print("=" * 60)
    print("📊 Test de récupération de données Saxo Bank")
    print("=" * 60)
    
    # Créer le client
    client = SaxoClient()
    
    # Charger les tokens
    print("\n🔐 Authentification...")
    if not client.ensure_authenticated():
        print("❌ Authentification échouée")
        print("⚠️  Exécutez: python authenticate_saxo.py")
        return
    
    print("✅ Authentifié avec succès")
    
    # Test 1: Récupérer les informations de compte
    print("\n" + "=" * 60)
    print("Test 1: Informations du compte")
    print("=" * 60)
    
    import requests
    
    headers = {
        'Authorization': f'Bearer {client.access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Récupérer les infos du compte
        response = requests.get(
            f"{client.base_url}/port/v1/accounts/me",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            account_data = response.json()
            print("✅ Compte récupéré:")
            print(f"   Client Key: {account_data.get('ClientKey', 'N/A')}")
            
            if 'Data' in account_data and len(account_data['Data']) > 0:
                account = account_data['Data'][0]
                account_key = account.get('AccountKey')
                print(f"   Account Key: {account_key}")
                print(f"   Account Type: {account.get('AccountType', 'N/A')}")
                print(f"   Currency: {account.get('Currency', 'N/A')}")
        else:
            print(f"⚠️  Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # Test 2: Rechercher un instrument (TotalEnergies)
    print("\n" + "=" * 60)
    print("Test 2: Recherche d'instrument - TotalEnergies (TTE)")
    print("=" * 60)
    
    try:
        # Rechercher TotalEnergies
        params = {
            'Keywords': 'TotalEnergies',
            'AssetTypes': 'Stock',
            'limit': 5
        }
        
        response = requests.get(
            f"{client.base_url}/ref/v1/instruments",
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            instruments = response.json()
            print(f"✅ {len(instruments.get('Data', []))} instrument(s) trouvé(s):\n")
            
            for inst in instruments.get('Data', [])[:3]:
                print(f"   Symbol: {inst.get('Symbol')}")
                print(f"   Description: {inst.get('Description')}")
                print(f"   Uic: {inst.get('Identifier')}")
                print(f"   Exchange: {inst.get('ExchangeId')}")
                print(f"   Currency: {inst.get('CurrencyCode')}")
                print()
                
                # Sauvegarder le premier UIC pour le test suivant
                if 'test_uic' not in locals():
                    test_uic = inst.get('Identifier')
                    test_symbol = inst.get('Symbol')
        else:
            print(f"⚠️  Status: {response.status_code}")
            print(f"   Response: {response.text}")
            test_uic = None
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        test_uic = None
    
    # Test 3: Récupérer les données de prix
    if test_uic:
        print("=" * 60)
        print(f"Test 3: Données de prix pour {test_symbol} (UIC: {test_uic})")
        print("=" * 60)
        
        try:
            # Récupérer le dernier prix
            params = {
                'Uic': test_uic,
                'AssetType': 'Stock'
            }
            
            response = requests.get(
                f"{client.base_url}/trade/v1/infoprices",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                price_data = response.json()
                print("✅ Prix actuel:")
                
                if 'Data' in price_data and len(price_data['Data']) > 0:
                    price_info = price_data['Data'][0]
                    quote = price_data.get('Quote', {})
                    
                    print(f"   Bid: {quote.get('Bid', 'N/A')}")
                    print(f"   Ask: {quote.get('Ask', 'N/A')}")
                    print(f"   Mid: {quote.get('Mid', 'N/A')}")
                    print(f"   Last: {quote.get('LastTraded', 'N/A')}")
            else:
                print(f"⚠️  Status: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    # Test 4: Récupérer des données historiques (charts)
    if test_uic:
        print("\n" + "=" * 60)
        print(f"Test 4: Données historiques (1 jour, 1 min)")
        print("=" * 60)
        
        try:
            params = {
                'Uic': test_uic,
                'AssetType': 'Stock',
                'Horizon': 60,  # 1 minute
                'Count': 100,   # 100 dernières bougies
                'Mode': 'UpTo'
            }
            
            response = requests.get(
                f"{client.base_url}/chart/v1/charts",
                headers=headers,
                params=params,
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                chart_data = response.json()
                print(f"✅ Données historiques récupérées:")
                print(f"   Data: {chart_data.keys()}")
                
                # Parser les données
                if 'Data' in chart_data:
                    candles = chart_data['Data']
                    print(f"   Nombre de bougies: {len(candles)}")
                    
                    if len(candles) > 0:
                        print(f"\n   Première bougie:")
                        first = candles[0]
                        print(f"      Time: {first.get('Time')}")
                        print(f"      Open: {first.get('Open')}")
                        print(f"      High: {first.get('High')}")
                        print(f"      Low: {first.get('Low')}")
                        print(f"      Close: {first.get('Close')}")
                        print(f"      Volume: {first.get('Volume')}")
                        
                        print(f"\n   Dernière bougie:")
                        last = candles[-1]
                        print(f"      Time: {last.get('Time')}")
                        print(f"      Open: {last.get('Open')}")
                        print(f"      High: {last.get('High')}")
                        print(f"      Low: {last.get('Low')}")
                        print(f"      Close: {last.get('Close')}")
                        print(f"      Volume: {last.get('Volume')}")
                        
                        # Créer un DataFrame
                        df = pd.DataFrame(candles)
                        print(f"\n   DataFrame créé:")
                        print(df.head())
                        
            else:
                print(f"⚠️  Status: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_historical_data()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
