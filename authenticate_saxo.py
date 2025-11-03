"""
Script d'authentification Saxo Bank avec serveur de callback automatique
"""
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Configuration
app_key = os.getenv("SAXO_APP_KEY")
app_secret = os.getenv("SAXO_APP_SECRET")
auth_url = os.getenv("SAXO_AUTH_URL")
token_url = os.getenv("SAXO_TOKEN_URL")
redirect_uri = os.getenv("SAXO_REDIRECT_URI")

# Variable pour stocker le code
authorization_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    """Handler pour capturer le callback OAuth2"""
    
    def log_message(self, format, *args):
        """Supprimer les logs automatiques"""
        pass
    
    def do_GET(self):
        """Gérer la requête GET du callback"""
        global authorization_code
        
        # Parser l'URL
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)
        
        if 'code' in params:
            authorization_code = params['code'][0]
            
            # Répondre au navigateur
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Authentification réussie</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">✅ Authentification réussie!</h1>
                <p>Vous pouvez fermer cette fenêtre.</p>
                <p>Le code a été capturé avec succès.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Erreur</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Erreur</h1>
                <p>Aucun code d'autorisation reçu.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())


def authenticate_saxo():
    """Authentification complète avec Saxo Bank"""
    global authorization_code
    
    print("=" * 60)
    print("🔐 Authentification Saxo Bank")
    print("=" * 60)
    
    # Étape 1: Construire l'URL d'autorisation
    auth_params = {
        'response_type': 'code',
        'client_id': app_key,
        'redirect_uri': redirect_uri,
        'state': 'boursicotor_auth'
    }
    
    full_auth_url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in auth_params.items()])}"
    
    print(f"\n📋 Configuration:")
    print(f"   App Key: {app_key[:8]}...{app_key[-4:]}")
    print(f"   Redirect URI: {redirect_uri}")
    
    print(f"\n🌐 Ouverture du navigateur pour l'authentification...")
    print(f"   URL: {full_auth_url}\n")
    
    # Démarrer le serveur de callback
    server = HTTPServer(('localhost', 8501), CallbackHandler)
    
    print("🔄 Serveur de callback démarré sur http://localhost:8501")
    print("⏳ En attente de l'autorisation...\n")
    
    # Ouvrir le navigateur
    webbrowser.open(full_auth_url)
    
    # Attendre le callback (timeout après 1 requête)
    server.handle_request()
    
    if not authorization_code:
        print("\n❌ Aucun code d'autorisation reçu")
        return False
    
    print(f"\n✅ Code d'autorisation reçu: {authorization_code[:20]}...")
    
    # Étape 2: Échanger le code contre des tokens
    print(f"\n🔄 Échange du code contre un access token...")
    
    data = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': redirect_uri,
        'client_id': app_key,
        'client_secret': app_secret
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            tokens = response.json()
            
            print("\n" + "=" * 60)
            print("✅ AUTHENTIFICATION RÉUSSIE!")
            print("=" * 60)
            
            access_token = tokens.get('access_token', '')
            refresh_token = tokens.get('refresh_token', '')
            expires_in = tokens.get('expires_in', 0)
            
            print(f"\n🔑 Access Token: {access_token[:50]}...")
            print(f"🔄 Refresh Token: {refresh_token}")
            print(f"⏱️  Expire dans: {expires_in} secondes ({expires_in//60} minutes)")
            
            # Calculer le timestamp d'expiration
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Sauvegarder les tokens
            with open('.saxo_tokens', 'w') as f:
                f.write(f"ACCESS_TOKEN={access_token}\n")
                f.write(f"REFRESH_TOKEN={refresh_token}\n")
                f.write(f"EXPIRES_IN={expires_in}\n")
                f.write(f"EXPIRES_AT={expires_at.isoformat()}\n")
            
            print(f"\n💾 Tokens sauvegardés dans .saxo_tokens")
            print(f"📅 Expire le: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Test rapide de l'API
            print(f"\n🧪 Test de l'API...")
            test_api(access_token)
            
            return True
        else:
            print(f"\n❌ Erreur: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors de l'échange: {e}")
        return False


def test_api(access_token):
    """Test simple de l'API Saxo Bank"""
    base_url = os.getenv("SAXO_BASE_URL")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test endpoint: récupérer les infos du compte
        response = requests.get(
            f"{base_url}/port/v1/accounts/me",
            headers=headers,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API fonctionne!")
            print(f"   Client Key: {data.get('ClientKey', 'N/A')}")
            print(f"   Accounts: {len(data.get('Data', []))} compte(s)")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
            print(f"   {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")


if __name__ == "__main__":
    try:
        print("\n⚠️  IMPORTANT: Fermez Streamlit si il tourne sur le port 8501\n")
        input("Appuyez sur Entrée pour continuer...")
        
        authenticate_saxo()
        
        print("\n" + "=" * 60)
        print("✅ Processus terminé!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Authentification annulée")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
