"""
Test pour vérifier la limite réelle de l'API Saxo Bank
Compare les limites en mode simulation vs production
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from brokers.saxo_client import SaxoClient
from backend.config import logger
import requests


def test_chart_api_limits():
    """
    Test la limite de l'API Chart pour différentes valeurs de Count
    """
    
    print("\n" + "="*70)
    print("TEST DES LIMITES DE L'API SAXO BANK CHART")
    print("="*70)
    print("\n⚠️  IMPORTANT:")
    print("Ce test vérifie si la limite de 1200 points est:")
    print("  - Une contrainte de l'API en général")
    print("  - Spécifique au compte de démonstration")
    print("  - Une limite arbitraire dans notre code\n")
    
    client = SaxoClient()
    
    if not client.ensure_authenticated():
        print("❌ Erreur: Impossible de s'authentifier")
        return
    
    # Récupérer l'UIC pour un instrument de test
    symbol = "GLE"
    uic = client.get_instrument_uic(symbol)
    
    if not uic:
        print(f"❌ Impossible de trouver l'UIC pour {symbol}")
        return
    
    print(f"✅ Test avec {symbol} (UIC: {uic})")
    print(f"📡 Mode: {'SIMULATION' if 'sim' in client.base_url else 'PRODUCTION'}")
    print(f"🔗 Base URL: {client.base_url}\n")
    
    # Tester différentes valeurs de Count
    test_counts = [
        100,      # Devrait fonctionner
        500,      # Devrait fonctionner
        1200,     # Limite actuelle dans notre code
        2000,     # Au-delà de la limite actuelle
        5000,     # Beaucoup plus
        10000,    # Très grand
    ]
    
    results = []
    
    for count in test_counts:
        print(f"\n🔍 Test avec Count = {count:,}")
        print("-" * 70)
        
        try:
            url = f"{client.base_url}/chart/v1/charts"
            
            params = {
                'AssetType': 'Stock',
                'Uic': uic,
                'Horizon': 3600,  # 1 heure
                'Count': count,
                'Mode': 'From'
            }
            
            headers = {
                'Authorization': f'Bearer {client.access_token}'
            }
            
            # Essayer GET
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 404:
                # Essayer POST si GET échoue
                body = {
                    'Arguments': {
                        'AssetType': 'Stock',
                        'Uic': uic,
                        'Horizon': 3600,
                        'Count': count
                    }
                }
                response = requests.post(url, json=body, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                data_points = len(data.get('Data', []))
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📊 Points reçus: {data_points:,}")
                
                if data_points < count:
                    print(f"   ⚠️  Moins de points que demandé ({count:,})")
                
                results.append({
                    'count': count,
                    'status': response.status_code,
                    'received': data_points,
                    'success': True
                })
                
            elif response.status_code == 404:
                print(f"   ℹ️  Status: 404 - Chart API non disponible (mode simulation)")
                print(f"   📝 C'est normal en mode simulation - l'API Chart n'est pas accessible")
                results.append({
                    'count': count,
                    'status': 404,
                    'received': 0,
                    'success': False,
                    'reason': 'Chart API not available in simulation'
                })
                # Si on a un 404, inutile de continuer les autres tests
                break
                
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📝 Erreur: {error_data}")
                
                results.append({
                    'count': count,
                    'status': response.status_code,
                    'received': 0,
                    'success': False,
                    'reason': str(error_data)
                })
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            results.append({
                'count': count,
                'status': 'Exception',
                'received': 0,
                'success': False,
                'reason': str(e)
            })
    
    # Résumé des résultats
    print("\n" + "="*70)
    print("RÉSUMÉ DES TESTS")
    print("="*70)
    
    print(f"\n{'Count':<10} {'Status':<10} {'Points Reçus':<15} {'Résultat':<15}")
    print("-" * 70)
    
    for result in results:
        status_str = str(result['status'])
        received_str = f"{result['received']:,}" if result['received'] > 0 else "-"
        success_str = "✅ Succès" if result['success'] else "❌ Échec"
        print(f"{result['count']:<10,} {status_str:<10} {received_str:<15} {success_str:<15}")
    
    # Conclusions
    print("\n" + "="*70)
    print("CONCLUSIONS")
    print("="*70)
    
    if any(r['status'] == 404 for r in results):
        print("\n⚠️  L'API Chart n'est PAS disponible en mode SIMULATION")
        print("\n📝 Explications:")
        print("   - En mode simulation, Saxo Bank ne donne pas accès à l'API Chart")
        print("   - Seules les APIs de référence et prix en temps réel sont disponibles")
        print("   - C'est pourquoi Boursicotor génère des données simulées")
        print("\n💡 Pour tester les vraies limites:")
        print("   - Vous auriez besoin d'un compte de production Saxo Bank")
        print("   - Ou d'un compte de démo avec accès complet aux APIs")
        print("\n🎯 Pour le backtesting et les stratégies:")
        print("   - Option 1: Utiliser les données simulées (actuellement implémenté)")
        print("   - Option 2: Importer des données d'autres sources (Yahoo Finance, etc.)")
        print("   - Option 3: Collecter progressivement via requêtes multiples")
        print("   - Option 4: Passer à un compte production pour tests réels")
        
    else:
        successful_tests = [r for r in results if r['success']]
        if successful_tests:
            max_successful = max(r['count'] for r in successful_tests)
            print(f"\n✅ Limite maximale testée avec succès: {max_successful:,} points")
            
            if max_successful >= 2000:
                print("\n🎉 Bonne nouvelle!")
                print(f"   La limite de 1200 dans notre code est ARTIFICIELLE")
                print(f"   L'API accepte au moins {max_successful:,} points")
                print("\n💡 Recommandation:")
                print("   - Augmenter la limite dans saxo_client.py")
                print("   - Tester avec des valeurs plus élevées")
                print("   - Adapter selon les besoins de backtesting")
        else:
            print("\n⚠️  Aucun test n'a réussi")
            print("   Impossible de déterminer la limite réelle")


if __name__ == "__main__":
    test_chart_api_limits()
