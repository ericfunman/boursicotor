"""
Saxo Bank Instrument Search Helper
Recherche d'actions sur le marché français
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from brokers.saxo_client import SaxoClient
from backend.config import logger


class SaxoInstrumentSearch:
    """Helper class to search French stocks on Saxo Bank"""
    
    def __init__(self):
        """Initialize with Saxo client"""
        self.client = SaxoClient()
    
    def search_french_stocks(self, query: str, limit: int = 20):
        """
        Search for French stocks by name or ticker
        
        Args:
            query: Search query (company name or ticker symbol)
            limit: Maximum number of results
            
        Returns:
            List of dicts with instrument info: [
                {
                    'ticker': 'GLE',
                    'name': 'Societe Generale SA',
                    'uic': 211,
                    'exchange': 'PAR',
                    'currency': 'EUR'
                },
                ...
            ]
        """
        try:
            # Ensure we're authenticated
            if not self.client.ensure_authenticated():
                logger.error("Failed to authenticate with Saxo Bank")
                return []
            
            # Remove accents for better search results
            import unicodedata
            query_normalized = ''.join(
                c for c in unicodedata.normalize('NFD', query)
                if unicodedata.category(c) != 'Mn'
            )
            
            # Search for the instrument
            url = f"{self.client.base_url}/ref/v1/instruments"
            params = {
                'AssetTypes': 'Stock',
                'Keywords': query_normalized.upper(),
                '$top': limit,
                'IncludeNonTradable': False
            }
            
            headers = {
                'Authorization': f'Bearer {self.client.access_token}'
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            instruments = data.get('Data', [])
            
            # Filter for French stocks (Euronext Paris)
            french_stocks = []
            for inst in instruments:
                # Look for Euronext Paris exchange
                exchange_id = inst.get('ExchangeId', '')
                symbol = inst.get('Symbol', '')
                
                # Common French exchanges: PAR (Paris), XPAR
                if 'PAR' in exchange_id or exchange_id.startswith('XPAR'):
                    # Extract UIC properly
                    uic = inst.get('Identifier')
                    if not uic:
                        uic = inst.get('Uic')
                    
                    french_stocks.append({
                        'ticker': symbol.split(':')[0] if ':' in symbol else symbol,
                        'name': inst.get('Description', ''),
                        'uic': uic,
                        'exchange': exchange_id,
                        'currency': inst.get('CurrencyCode', 'EUR'),
                        'isin': inst.get('Isin', '')
                    })
            
            logger.info(f"Found {len(french_stocks)} French stocks for query '{query}'")
            return french_stocks
            
        except Exception as e:
            logger.error(f"Error searching for instruments: {e}")
            return []
    
    def get_instrument_details(self, ticker: str):
        """
        Get detailed information for a specific ticker
        
        Args:
            ticker: The ticker symbol (e.g., 'GLE', 'MC', 'OR')
            
        Returns:
            Dict with instrument details or None if not found
        """
        results = self.search_french_stocks(ticker, limit=10)
        
        # Try to find exact match
        for result in results:
            if result['ticker'].upper() == ticker.upper():
                return result
        
        # If no exact match, return first result
        if results:
            logger.warning(f"No exact match for '{ticker}', returning closest match")
            return results[0]
        
        return None


def test_search():
    """Test the search functionality"""
    searcher = SaxoInstrumentSearch()
    
    # Test queries
    test_queries = [
        'GLE',           # Société Générale
        'MC',            # LVMH
        'OR',            # L'Oréal
        'TTE',           # TotalEnergies
        'BNP',           # BNP Paribas
        'LVMH',          # LVMH (by name)
        'Total',         # TotalEnergies (by name)
        'Société Générale'  # Full name
    ]
    
    print("\n" + "="*60)
    print("TEST DE RECHERCHE D'ACTIONS FRANÇAISES")
    print("="*60)
    
    for query in test_queries:
        print(f"\n🔍 Recherche: '{query}'")
        print("-" * 60)
        
        results = searcher.search_french_stocks(query, limit=5)
        
        if results:
            print(f"✅ {len(results)} résultat(s) trouvé(s):\n")
            for i, stock in enumerate(results, 1):
                print(f"{i}. {stock['ticker']} - {stock['name']}")
                print(f"   UIC: {stock['uic']} | Exchange: {stock['exchange']} | {stock['currency']}")
                if stock.get('isin'):
                    print(f"   ISIN: {stock['isin']}")
        else:
            print("❌ Aucun résultat")
        
        print()


if __name__ == "__main__":
    test_search()
