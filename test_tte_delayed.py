#!/usr/bin/env python3
"""Test real-time (delayed) market data retrieval for TTE (European stock)"""

from ib_insync import IB, Stock
from loguru import logger
import time

logger.add("test_tte_delayed.log", level="INFO")

def test_real_time_data():
    logger.info("=" * 80)
    logger.info("Testing delayed market data retrieval for TTE (European stock)")
    logger.info("=" * 80)
    
    ib = IB()
    
    try:
        logger.info("Connecting to IBKR on port 4002 with clientId=999..")
        ib.connect("127.0.0.1", 4002, clientId=999)
        logger.info("✅ Connected to IBKR")
        
        # Test with TTE (European stock) instead of TSLA
        tte_contract = Stock("TTE", "SMART", "EUR")
        
        logger.info("")
        logger.info("--- TTE (European stock - testing delayed data) ---")
        logger.info(f"Requesting market data for: {tte_contract}")
        
        # Subscribe to market data
        ticker = ib.reqMktData(tte_contract)
        time.sleep(0.5)  # Give IB a moment to start
        
        # Test with 10 attempts over 5 seconds
        for attempt in range(1, 11):
            logger.info("")
            logger.info(f"Attempt {attempt}:")
            logger.info(f"  last: {ticker.last}")
            logger.info(f"  bid: {ticker.bid}")
            logger.info(f"  ask: {ticker.ask}")
            logger.info(f"  close: {ticker.close}")
            logger.info(f"  volume: {ticker.volume}")
            logger.info(f"  time: {ticker.time}")
            
            # Check if we got any data
            if ticker.last is not None and not (isinstance(ticker.last, float) and ticker.last != ticker.last):
                # last is not None and not NaN
                logger.info(f"  ✅ Got real data for TTE!")
                break
            else:
                logger.info(f"  ⏳ Still waiting for data...")
            
            time.sleep(0.5)
        
        # Cancel subscription
        ib.cancelMktData(tte_contract)
        
    finally:
        ib.disconnect()
        logger.info("\n✅ Test completed")

if __name__ == "__main__":
    test_real_time_data()
