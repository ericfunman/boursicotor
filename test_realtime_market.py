#!/usr/bin/env python3
"""
Test script to get real-time market data from IBKR
"""
import sys
import time
from ib_insync import IB, Stock
from backend.config import logger

def test_real_time_data():
    """Test getting real-time market data from IBKR using reqMktData"""
    
    logger.info("=" * 60)
    logger.info("Testing real-time market data retrieval")
    logger.info("=" * 60)
    
    ib = IB()
    
    try:
        logger.info("Connecting to IBKR on port 4002 with clientId=999...")
        ib.connect('127.0.0.1', 4002, clientId=999)
        logger.info("✅ Connected to IBKR")
        time.sleep(1)
        
        # Test with TSLA (US stock)
        tsla = Stock('TSLA', 'SMART', 'USD')
        
        logger.info(f"\n--- TSLA (testing real-time market data) ---")
        
        # Request market data
        logger.info("Requesting market data...")
        ib.reqMktData(tsla, '', False, False)
        
        # Try 5 attempts to get data
        for attempt in range(5):
            time.sleep(1)
            ticker = ib.ticker(tsla)
            
            logger.info(f"\nAttempt {attempt + 1}:")
            logger.info(f"  last: {ticker.last}")
            logger.info(f"  bid: {ticker.bid}")
            logger.info(f"  ask: {ticker.ask}")
            logger.info(f"  close: {ticker.close}")
            logger.info(f"  volume: {ticker.volume}")
            logger.info(f"  time: {ticker.time}")
            
            # Check if we got real data
            if ticker.last > 0 and ticker.last != float('nan'):
                logger.info(f"  ✅ GOT REAL DATA: {ticker.last}")
                break
            else:
                logger.info(f"  ⏳ Still waiting for data...")
        
        # Cancel market data
        ib.cancelMktData(tsla)
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        ib.disconnect()

if __name__ == "__main__":
    success = test_real_time_data()
    sys.exit(0 if success else 1)
