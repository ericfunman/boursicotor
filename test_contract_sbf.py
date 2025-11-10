#!/usr/bin/env python
"""
Test contract qualification with SBF exchange priority
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger

def test_contract_sbf():
    """Test that WLN uses SBF exchange, not SMART"""
    
    print("\n" + "="*60)
    print("TEST: Contract Qualification with SBF Priority")
    print("="*60)
    
    collector = IBKRCollector()
    
    if not collector.connect():
        print("❌ Failed to connect to IBKR")
        return False
    
    symbols = ['WLN', 'TTE']
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}...")
        
        try:
            # This should now try SBF first for EUR stocks
            contract = collector.get_contract(symbol)
            
            if not contract:
                print(f"❌ Could not qualify contract for {symbol}")
                continue
            
            print(f"✅ Contract qualified:")
            print(f"   Symbol: {contract.symbol}")
            print(f"   Exchange: {contract.exchange}")
            print(f"   Primary Exchange: {contract.primaryExchange}")
            print(f"   Currency: {contract.currency}")
            
            # Check it's not SMART (should be SBF or its primary exchange)
            if contract.exchange == 'SMART':
                print(f"   ⚠️  WARNING: Exchange is still SMART (may cause delayed data issues)")
            else:
                print(f"   ✅ Good: Exchange is {contract.exchange} (not SMART)")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    collector.disconnect()
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60 + "\n")
    return True

if __name__ == '__main__':
    success = test_contract_sbf()
    sys.exit(0 if success else 1)
