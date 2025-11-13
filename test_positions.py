#!/usr/bin/env python3
"""
Test script to get real-time market data from IBKR
"""
import sys
import time
from ib_insync import IB, Stock
from backend.config import logger

def test_realtime_market_data():
    """Test getting real-time market data from IBKR using reqMktData"""
    
    logger.info("=" * 60)
    logger.info("Testing real-time market data with reqMktData()")
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
        
        for contract in [tte, wln]:
            logger.info(f"\n--- {contract.symbol} ---")
            
            try:
                # Request real-time market data
                logger.info("Requesting real-time market data with reqMktData()...")
                ib.reqMktData(contract, '', False, False)
                
                # Wait for data to arrive (up to 5 seconds)
                for attempt in range(10):
                    time.sleep(0.5)
                    ticker = ib.ticker(contract)
                    
                    logger.info(f"\nAttempt {attempt+1}:")
                    logger.info(f"  last: {ticker.last}")
                    logger.info(f"  bid: {ticker.bid}")
                    logger.info(f"  ask: {ticker.ask}")
                    logger.info(f"  close: {ticker.close}")
                    logger.info(f"  volume: {ticker.volume}")
                    logger.info(f"  time: {ticker.time}")
                    
                    # Check if we got valid data
                    if ticker.last > 0 and ticker.last != float('nan'):
                        logger.info(f"✅ GOT REAL-TIME DATA: {ticker.last}€")
                        break
                    elif ticker.bid > 0 and ticker.ask > 0:
                        midpoint = (ticker.bid + ticker.ask) / 2
                        logger.info(f"✅ GOT BID/ASK: midpoint = {midpoint}€")
                        break
                
                # Cancel the subscription
                ib.cancelMktData(contract)
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  Error: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        ib.disconnect()

if __name__ == "__main__":
    success = test_realtime_market_data()
    sys.exit(0 if success else 1)
