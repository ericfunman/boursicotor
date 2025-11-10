#!/usr/bin/env python
"""Module documentation."""

"""
Test market data with delayed data (free IBKR subscription)
Verifies that 'close' field is populated even when 'last' is not available
"""
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger

def test_delayed_data():
    """Test requesting market data with delayed data access"""
    
    print("\n" + "="*60)
    print("TEST: Market Data with Delayed Data (Free Tier)")
    print("="*60)
    
    collector = IBKRCollector()
    
    if not collector.connect():
        print("❌ Failed to connect to IBKR")
        return False
    
    # Test with WLN (as user reported)
    symbol = 'WLN'
    
    print(f"\n📊 Testing market data request for {symbol}...")
    
    try:
        contract = collector.get_contract(symbol)
        if not contract:
            print(f"❌ Could not qualify contract for {symbol}")
            collector.disconnect()
            return False
        
        print(f"✅ Contract qualified: {contract.symbol} on {contract.primaryExchange}")
        
        # Request market data (will get delayed data if not subscribed)
        print(f"\n📡 Requesting market data for {symbol}...")
        ticker_data = collector.ib.reqMktData(contract, '', False, False)
        
        # Wait for data to arrive
        print("⏳ Waiting for market data (delayed data may take 2-5 seconds)...")
        for i in range(15):  # Wait up to 7.5 seconds
            if ticker_data.last > 0 or ticker_data.close > 0:
                print(f"✅ Got data after {i*0.5:.1f} seconds")
                break
            print(f"   Waiting... ({(i+1)*0.5:.1f}s)", end='\r')
            collector.ib.sleep(0.5)
        
        # Print available data
        print("\n📋 Market Data Available:")
        print(f"   Symbol: {symbol}")
        print(f"   Last:     {ticker_data.last} {'✅' if ticker_data.last > 0 else '❌'}")
        print(f"   Close:    {ticker_data.close} {'✅' if ticker_data.close > 0 else '❌'}")
        print(f"   Open:     {ticker_data.open} {'✅' if ticker_data.open > 0 else '❌'}")
        print(f"   High:     {ticker_data.high} {'✅' if ticker_data.high > 0 else '❌'}")
        print(f"   Low:      {ticker_data.low} {'✅' if ticker_data.low > 0 else '❌'}")
        print(f"   Volume:   {ticker_data.volume} {'✅' if ticker_data.volume > 0 else '❌'}")
        print(f"   Bid:      {ticker_data.bid} {'✅' if ticker_data.bid > 0 else '❌'}")
        print(f"   Ask:      {ticker_data.ask} {'✅' if ticker_data.ask > 0 else '❌'}")
        
        # Check what we can use
        price = ticker_data.last if ticker_data.last > 0 else ticker_data.close
        if price > 0:
            print(f"\n✅ SOLUTION: Use price = {price}€")
            print("   (Falls back from 'last' to 'close' for delayed data)")
        else:
            print("\n❌ No price data available!")
            return False
        
        # Cancel subscription
        collector.ib.cancelMktData(contract)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        collector.disconnect()
    
    print("\n" + "="*60)
    print("✅ TEST PASSED: Delayed data is working correctly!")
    print("="*60 + "\n")
    return True

if __name__ == '__main__':
    success = test_delayed_data()
    sys.exit(0 if success else 1)
