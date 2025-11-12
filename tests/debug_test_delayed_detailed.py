#!/usr/bin/env python
"""Module documentation."""

"""
Test delayed data access with detailed diagnostics
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger
from ib_insync import Stock

def test_delayed_data_detailed():
    """Test delayed data with SBF exchange"""
    
    print("\n" + "="*70)
    print("TEST: Delayed Data Access - Detailed Diagnostics")
    print("="*70)
    
    collector = IBKRCollector()
    
    if not collector.connect():
        print("❌ Failed to connect to IBKR")
        return False
    
    symbol = 'WLN'
    
    print(f"\n1️⃣  Testing with new get_contract() - should try SBF first...")
    try:
        contract = collector.get_contract(symbol)
        if contract:
            print(f"✅ Contract obtained:")
            print(f"   Symbol: {contract.symbol}")
            print(f"   Exchange: {contract.exchange}")
            print(f"   Primary Exchange: {contract.primaryExchange}")
            print(f"   ConId: {contract.conId}")
        else:
            print(f"❌ Contract qualification failed")
            collector.disconnect()
            return False
    except Exception as e:
        print(f"❌ Error getting contract: {e}")
        collector.disconnect()
        return False
    
    print(f"\n2️⃣  Requesting market data...")
    try:
        ticker_data = collector.ib.reqMktData(contract, '', False, False)
        print(f"✅ Market data request sent")
        print(f"   Waiting for data to arrive...")
        
        for i in range(20):  # Wait up to 10 seconds
            if ticker_data.last > 0 or ticker_data.close > 0:
                print(f"✅ DATA RECEIVED after {i*0.5:.1f}s")
                break
            elif i % 4 == 0:
                print(f"   ... {i*0.5:.1f}s ...")
            collector.ib.sleep(0.5)
        
        print(f"\n3️⃣  Market data fields:")
        print(f"   Last:     {ticker_data.last}")
        print(f"   Close:    {ticker_data.close}")
        print(f"   Open:     {ticker_data.open}")
        print(f"   High:     {ticker_data.high}")
        print(f"   Low:      {ticker_data.low}")
        print(f"   Bid:      {ticker_data.bid}")
        print(f"   Ask:      {ticker_data.ask}")
        print(f"   Volume:   {ticker_data.volume}")
        print(f"   Time:     {ticker_data.time}")
        
        # Check what we can use
        price = ticker_data.last if ticker_data.last > 0 else ticker_data.close
        if price > 0:
            print(f"\n✅ SUCCESS: Got price = {price}€")
        else:
            print(f"\n❌ FAILED: No price data available")
        
        # Cancel subscription
        collector.ib.cancelMktData(contract)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    collector.disconnect()
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70 + "\n")
    return True

if __name__ == '__main__':
    success = test_delayed_data_detailed()
    sys.exit(0 if success else 1)
