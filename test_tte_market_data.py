#!/usr/bin/env python3
"""Test market data retrieval for TTE with proper waiting"""

from ib_insync import IB, Stock
from loguru import logger
import time

logger.add("test_tte_market.log", level="INFO")

def test_market_data_with_wait():
    logger.info("=" * 80)
    logger.info("Testing market data for TTE (European stock)")
    logger.info("=" * 80)
    
    ib = IB()
    
    try:
        logger.info("Connecting to IBKR...")
        ib.connect("127.0.0.1", 4002, clientId=999)
        logger.info("✅ Connected")
        
        # Create TTE contract
        tte_contract = Stock("TTE", "SMART", "EUR")
        logger.info(f"Contract: {tte_contract}")
        
        # Request market data
        logger.info("\nRequesting market data...")
        ticker = ib.reqMktData(tte_contract)
        
        # IMPORTANT: Wait longer for data to arrive from broker
        logger.info("Waiting for market data to arrive (this can take 2-5 seconds)...")
        
        for attempt in range(1, 21):  # 20 attempts * 0.5s = 10 seconds max
            time.sleep(0.5)
            
            # Check all possible price fields
            logger.info(f"\nAttempt {attempt}:")
            logger.info(f"  last: {ticker.last}")
            logger.info(f"  bid: {ticker.bid}")
            logger.info(f"  ask: {ticker.ask}")
            logger.info(f"  close: {ticker.close}")
            logger.info(f"  open: {ticker.open}")
            logger.info(f"  high: {ticker.high}")
            logger.info(f"  low: {ticker.low}")
            logger.info(f"  volume: {ticker.volume}")
            logger.info(f"  time: {ticker.time}")
            
            # Check if we got valid data (not NaN)
            import math
            has_valid_last = ticker.last is not None and not math.isnan(ticker.last) if isinstance(ticker.last, float) else ticker.last is not None
            has_valid_bid = ticker.bid is not None and not math.isnan(ticker.bid) if isinstance(ticker.bid, float) else ticker.bid is not None
            
            if has_valid_last or has_valid_bid:
                logger.info(f"  ✅ Got market data!")
                logger.info(f"  Time elapsed: {attempt * 0.5}s")
                break
            else:
                logger.info(f"  ⏳ Waiting for data...")
        
        # Cancel subscription
        ib.cancelMktData(tte_contract)
        logger.info("\n✅ Market data subscription cancelled")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        ib.disconnect()
        logger.info("Disconnected")

if __name__ == "__main__":
    test_market_data_with_wait()
