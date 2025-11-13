#!/usr/bin/env python3
"""
Test script to debug market data retrieval from IBKR
"""
import sys
import time
from ib_insync import IB, Stock
from backend.config import logger

def test_market_data():
    """Test getting market data from IBKR using historical data"""
    
    logger.info("=" * 60)
    logger.info("Testing historical data retrieval (1 day = most recent)")
    logger.info("=" * 60)
    
    ib = IB()
    
    try:
        logger.info("Connecting to IBKR on port 4002 with clientId=999...")
        ib.connect('127.0.0.1', 4002, clientId=999)
        logger.info("✅ Connected to IBKR")
        time.sleep(1)
        
        # Create contracts
        tte = Stock('TTE', 'SMART', 'EUR')
        wln = Stock('WLN', 'SMART', 'EUR')
        
        for contract, expected_price in [(tte, 55.7), (wln, 1.94)]:
            logger.info(f"\n--- {contract.symbol} (expected ~{expected_price}€) ---")
            
            try:
                # Get 1 day of historical data (most recent bar)
                bars = ib.reqHistoricalData(
                    contract,
                    endDateTime='',  # Most recent
                    durationStr='1 D',  # 1 day
                    barSizeSetting='1 day',  # 1 day bars
                    whatToShow='TRADES',
                    useRTH=False,
                    formatDate=1
                )
                
                logger.info(f"  Got {len(bars)} bars")
                
                if bars:
                    latest_bar = bars[-1]  # Most recent bar
                    logger.info(f"  Date: {latest_bar.date}")
                    logger.info(f"  Open: {latest_bar.open}")
                    logger.info(f"  High: {latest_bar.high}")
                    logger.info(f"  Low: {latest_bar.low}")
                    logger.info(f"  Close: {latest_bar.close} 💚 PRICE")
                    logger.info(f"  Volume: {latest_bar.volume}")
                else:
                    logger.info("  ❌ No bars returned")
                    
            except Exception as e:
                logger.error(f"  Error getting historical data: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        ib.disconnect()

if __name__ == "__main__":
    success = test_market_data()
    sys.exit(0 if success else 1)
