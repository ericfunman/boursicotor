#!/usr/bin/env python
"""
Test portfolio prices fallback
Verifies we can get prices from portfolio when market data fails
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger

def test_portfolio_prices():
    """Test getting prices from portfolio"""
    
    print("\n" + "="*70)
    print("TEST: Portfolio Prices as Fallback for Live Data")
    print("="*70)
    
    collector = IBKRCollector()
    
    if not collector.connect():
        print("❌ Failed to connect to IBKR")
        return False
    
    print(f"\n1️⃣  Getting portfolio...")
    
    try:
        portfolio = collector.ib.portfolio()
        
        if not portfolio:
            print("❌ Portfolio is empty")
            collector.disconnect()
            return False
        
        print(f"✅ Portfolio found with {len(portfolio)} position(s):\n")
        
        for item in portfolio:
            symbol = item.contract.symbol
            market_price = item.marketPrice
            position = item.position
            market_value = item.marketValue
            
            print(f"   📊 {symbol}")
            print(f"      Position: {position}")
            print(f"      Price: {market_price}€")
            print(f"      Value: {market_value}€")
        
        print(f"\n✅ SUCCESS: Can use portfolio prices as fallback source!")
        print(f"   For symbols: {', '.join([item.contract.symbol for item in portfolio])}")
        
    except Exception as e:
        print(f"❌ Error getting portfolio: {e}")
        import traceback
        traceback.print_exc()
        collector.disconnect()
        return False
    
    collector.disconnect()
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70 + "\n")
    return True

if __name__ == '__main__':
    success = test_portfolio_prices()
    sys.exit(0 if success else 1)
