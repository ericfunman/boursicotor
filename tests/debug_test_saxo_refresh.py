"""
Test du refresh automatique du token Saxo Bank
"""
import time
from brokers.saxo_client import SaxoClient
from backend.config import logger

def test_token_refresh():
    """Test le mécanisme de refresh automatique"""
    print("=" * 60)
    print("🧪 Test du Refresh Token Automatique")
    print("=" * 60)
    
    # Créer le client
    client = SaxoClient()
    
    # Charger les tokens existants
    print("\n📂 Chargement des tokens...")
    if client._load_tokens():
        print("✅ Tokens chargés avec succès")
        print(f"   Access Token: {client.access_token[:30]}..." if client.access_token else "   No token")
        print(f"   Refresh Token: {client.refresh_token}" if client.refresh_token else "   No refresh token")
        print(f"   Expire à: {client.token_expires_at}" if client.token_expires_at else "   No expiration")
        print(f"   Connecté: {client.connected}")
    else:
        print("❌ Impossible de charger les tokens")
        print("⚠️  Exécutez d'abord: python authenticate_saxo.py")
        return
    
    # Test 1: Vérifier ensure_authenticated
    print("\n" + "=" * 60)
    print("Test 1: Vérification de l'authentification")
    print("=" * 60)
    
    if client.ensure_authenticated():
        print("✅ Authentifié avec succès")
    else:
        print("❌ Échec de l'authentification")
        return
    
    # Test 2: Forcer un refresh du token
    print("\n" + "=" * 60)
    print("Test 2: Refresh manuel du token")
    print("=" * 60)
    
    old_token = client.access_token
    print(f"Ancien token: {old_token[:30]}...")
    
    print("\n🔄 Refresh en cours...")
    if client.refresh_access_token():
        print("✅ Token refreshé avec succès")
        print(f"Nouveau token: {client.access_token[:30]}...")
        
        if old_token != client.access_token:
            print("✅ Le token a bien changé")
        else:
            print("⚠️  Le token est identique (normal pour Saxo Bank)")
            
        print(f"Expire à: {client.token_expires_at}")
    else:
        print("❌ Échec du refresh")
        return
    
    # Test 3: Test d'un appel API
    print("\n" + "=" * 60)
    print("Test 3: Appel API avec le token refreshé")
    print("=" * 60)
    
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
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API fonctionne avec le nouveau token!")
            print(f"Client Key: {data.get('ClientKey', 'N/A')}")
            print(f"Nombre de comptes: {len(data.get('Data', []))}")
        else:
            print(f"⚠️  Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erreur API: {e}")
    
    # Test 4: Test de ensure_authenticated avec token valide
    print("\n" + "=" * 60)
    print("Test 4: ensure_authenticated ne devrait pas refresh")
    print("=" * 60)
    
    token_before = client.access_token
    client.ensure_authenticated()
    
    if token_before == client.access_token:
        print("✅ Token inchangé (normal, il n'expire pas encore)")
    else:
        print("⚠️  Token a changé (le token expirait bientôt)")
    
    print("\n" + "=" * 60)
    print("✅ Tous les tests terminés!")
    print("=" * 60)
    
    print("\n📊 Résumé:")
    print(f"   Access Token: {client.access_token[:30]}...")
    print(f"   Refresh Token: {client.refresh_token}")
    print(f"   Expire à: {client.token_expires_at}")
    print(f"   Connecté: {client.connected}")
    
    # Calculer le temps restant
    if client.token_expires_at:
        from datetime import datetime
        time_left = client.token_expires_at - datetime.now()
        minutes_left = int(time_left.total_seconds() / 60)
        print(f"   ⏰ Temps restant: {minutes_left} minutes")


if __name__ == "__main__":
    try:
        test_token_refresh()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
