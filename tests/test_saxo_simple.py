"""
Test simple de récupération de données avec la nouvelle méthode
"""
from brokers.saxo_client import SaxoClient
from backend.config import logger

def test_get_data():
    """Test simple"""
    print("=" * 60)
    print("📊 Test de récupération de données TotalEnergies")
    print("=" * 60)
    
    # Créer le client
    client = SaxoClient()
    
    # Authentifier
    print("\n🔐 Authentification...")
    if not client.ensure_authenticated():
        print("❌ Échec authentification")
        return
    print("✅ Authentifié")
    
    # Test 1: Récupérer les données historiques
    print("\n" + "=" * 60)
    print("Test: Données historiques TTE (1 jour, 5 minutes)")
    print("=" * 60)
    
    df = client.get_historical_data(
        symbol='TTE',
        duration='1D',
        bar_size='5min'
    )
    
    if df is not None and len(df) > 0:
        print(f"\n✅ Données récupérées: {len(df)} bougies")
        print(f"\nPremières lignes:")
        print(df.head())
        print(f"\nDernières lignes:")
        print(df.tail())
        print(f"\nStatistiques:")
        print(df.describe())
    else:
        print("\n❌ Aucune donnée récupérée")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_get_data()
