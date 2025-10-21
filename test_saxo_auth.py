"""
Script de test pour l'authentification Saxo Bank
"""
import os
from dotenv import load_dotenv
from brokers.saxo_client import SaxoClient
from backend.config import logger

# Charger les variables d'environnement
load_dotenv()

def test_saxo_authentication():
    """Test l'authentification Saxo Bank"""
    print("=" * 60)
    print("🔐 Test d'authentification Saxo Bank")
    print("=" * 60)
    
    # Créer le client
    client = SaxoClient()
    
    print(f"\n📋 Configuration:")
    print(f"   Base URL: {client.base_url}")
    print(f"   Auth URL: {client.auth_url}")
    print(f"   Token URL: {client.token_url}")
    print(f"   App Key: {client.app_key[:8]}...{client.app_key[-4:]}" if client.app_key else "   App Key: NOT SET")
    print(f"   Redirect URI: {client.redirect_uri}")
    
    # Étape 1: Obtenir l'URL d'autorisation
    print("\n" + "=" * 60)
    print("📝 ÉTAPE 1: Autorisation")
    print("=" * 60)
    print("\n⚠️  Veuillez suivre ces étapes:\n")
    
    # Construire l'URL d'autorisation
    auth_params = {
        'response_type': 'code',
        'client_id': client.app_key,
        'redirect_uri': client.redirect_uri,
        'state': 'test_auth_123'
    }
    
    auth_url = f"{client.auth_url}?{'&'.join([f'{k}={v}' for k, v in auth_params.items()])}"
    
    print(f"1️⃣  Ouvrez cette URL dans votre navigateur:\n")
    print(f"   {auth_url}\n")
    print(f"2️⃣  Connectez-vous avec vos identifiants Saxo Bank")
    print(f"3️⃣  Autorisez l'application")
    print(f"4️⃣  Vous serez redirigé vers: {client.redirect_uri}?code=XXX")
    print(f"5️⃣  Copiez le CODE de l'URL (la partie après 'code=')")
    
    print("\n" + "=" * 60)
    auth_code = input("\n📥 Collez le code d'autorisation ici: ").strip()
    
    if not auth_code:
        print("❌ Aucun code fourni. Abandon.")
        return False
    
    # Étape 2: Échanger le code contre un token
    print("\n" + "=" * 60)
    print("🔄 ÉTAPE 2: Échange du code contre un token...")
    print("=" * 60)
    
    success = client.authenticate(authorization_code=auth_code)
    
    if success:
        print("\n✅ AUTHENTIFICATION RÉUSSIE!")
        print(f"   Access Token: {client.access_token[:20]}..." if client.access_token else "   No token")
        print(f"   Refresh Token: {client.refresh_token[:20]}..." if client.refresh_token else "   No refresh token")
        print(f"   Connected: {client.connected}")
        
        # Étape 3: Test simple d'API
        print("\n" + "=" * 60)
        print("🧪 ÉTAPE 3: Test d'un appel API...")
        print("=" * 60)
        
        # On peut tester un endpoint simple comme /port/v1/accounts
        import requests
        
        headers = {
            'Authorization': f'Bearer {client.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{client.base_url}/port/v1/accounts/me",
                headers=headers,
                timeout=30
            )
            
            print(f"\n   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API fonctionne!")
                print(f"   Données: {data}")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Erreur API: {e}")
        
        return True
    else:
        print("\n❌ AUTHENTIFICATION ÉCHOUÉE")
        return False


if __name__ == "__main__":
    try:
        test_saxo_authentication()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
