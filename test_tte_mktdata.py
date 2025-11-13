#!/usr/bin/env python3
"""Test market data retrieval for TTE with proper waiting"""

from ib_insync import IB, Stock
from loguru import logger
import time

logger.add("test_tte_mktdata.log", level="INFO")

def test_tte_market_data():
    logger.info("=" * 80)
    logger.info("Testing market data (15min delayed) for TTE")
    logger.info("=" * 80)
    
    ib = IB()
    
    try:
        logger.info("Connecting to IBKR on port 4002 with clientId=999..")
        ib.connect("127.0.0.1", 4002, clientId=999)
        logger.info("✅ Connected to IBKR\n")
        
        # Create TTE contract
        tte_contract = Stock("TTE", "SMART", "EUR")
        logger.info(f"Contract: {tte_contract}")
        
        # Subscribe to market data
        logger.info("Subscribing to market data...")
        ticker = ib.reqMktData(tte_contract)
        
        # Wait for data to arrive (give it plenty of time)
        logger.info("Waiting for market data to arrive (up to 10 seconds)...\n")
        
        for i in range(20):
            time.sleep(0.5)
            
            # Check if we have real data (not NaN)
            has_bid = ticker.bid is not None and ticker.bid == ticker.bid  # NaN check
            has_ask = ticker.ask is not None and ticker.ask == ticker.ask
            has_last = ticker.last is not None and ticker.last == ticker.last
            
            if i % 4 == 0:  # Log every 2 seconds
                logger.info(f"[{i*0.5:.1f}s] bid={ticker.bid}, ask={ticker.ask}, last={ticker.last}")
            
            if (has_bid or has_ask or has_last):
                logger.info(f"\n✅ Got market data after {i*0.5:.1f} seconds!")
                logger.info(f"   bid: {ticker.bid}")
                logger.info(f"   ask: {ticker.ask}")
                logger.info(f"   last: {ticker.last}")
                logger.info(f"   close: {ticker.close}")
                logger.info(f"   time: {ticker.time}")
                break
        else:
            logger.warning("❌ No market data received after 10 seconds")
        
        # Clean up
        ib.cancelMktData(tte_contract)
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        ib.disconnect()
        logger.info("✅ Disconnected")

if __name__ == "__main__":
    test_tte_market_data()
