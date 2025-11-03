"""
Script pour échanger le code d'autorisation contre un access token
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Votre code d'autorisation
authorization_code = "53308420-5ac0-444e-99fb-5eb687a79a8d"

# Configuration
token_url = os.getenv("SAXO_TOKEN_URL")
app_key = os.getenv("SAXO_APP_KEY")
app_secret = os.getenv("SAXO_APP_SECRET")
redirect_uri = os.getenv("SAXO_REDIRECT_URI")

print("=" * 60)
print("🔄 Échange du code contre un access token")
print("=" * 60)
print(f"\nToken URL: {token_url}")
print(f"App Key: {app_key[:8]}...{app_key[-4:]}")
print(f"Redirect URI: {redirect_uri}")
print(f"Code: {authorization_code}")

# Préparer la requête
data = {
    'grant_type': 'authorization_code',
    'code': authorization_code,
    'redirect_uri': redirect_uri,
    'client_id': app_key,
    'client_secret': app_secret
}

print("\n🔄 Envoi de la requête...")

try:
    response = requests.post(token_url, data=data, timeout=30)
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📝 Response:\n{response.text}\n")
    
    if response.status_code in [200, 201]:
        tokens = response.json()
        
        print("=" * 60)
        print("✅ SUCCÈS! Tokens reçus:")
        print("=" * 60)
        print(f"\n🔑 Access Token: {tokens.get('access_token', 'N/A')[:50]}...")
        print(f"🔄 Refresh Token: {tokens.get('refresh_token', 'N/A')[:50]}...")
        print(f"⏱️  Expires In: {tokens.get('expires_in', 'N/A')} secondes")
        print(f"📋 Token Type: {tokens.get('token_type', 'N/A')}")
        
        # Sauvegarder les tokens dans un fichier
        with open('.saxo_tokens', 'w') as f:
            f.write(f"ACCESS_TOKEN={tokens.get('access_token')}\n")
            f.write(f"REFRESH_TOKEN={tokens.get('refresh_token')}\n")
            f.write(f"EXPIRES_IN={tokens.get('expires_in')}\n")
        
        print("\n💾 Tokens sauvegardés dans .saxo_tokens")
        print("\n✅ Vous pouvez maintenant utiliser l'API Saxo Bank!")
        
    else:
        print("=" * 60)
        print("❌ ERREUR lors de l'échange du code")
        print("=" * 60)
        print("\n⚠️  Vérifiez:")
        print("  - Le code n'a pas expiré (valide ~10 minutes)")
        print("  - L'App Key et App Secret sont corrects")
        print("  - La Redirect URI correspond exactement")
        
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
