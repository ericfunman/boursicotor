"""
Test script for live price collection loop
Validates the logic before putting it in the thread
"""
import time
from ib_insync import IB, Stock
from backend.config import logger

def test_live_price_loop():
    """Test collecting prices in a loop - SAME LOGIC AS DASHBOARD"""
    symbol = "TTE"
    
    # Create ONE persistent connection
    ib = IB()
    logger.info(f"Connecting to IBKR...")
    ib.connect('127.0.0.1', 4002, clientId=201)
    
    # Wait for connection
    for i in range(20):
        time.sleep(0.2)
        if ib.isConnected():
            logger.info(f"✅ Connected after {(i+1)*0.2:.1f}s")
            break
    
    if not ib.isConnected():
        logger.error("Failed to connect to IBKR")
        return
    
    logger.info(f"Starting price collection loop for {symbol}...")
    
    # Loop and collect prices - SAME LOGIC AS DASHBOARD
    for i in range(10):  # 10 iterations
        try:
            # Create fresh contract (like dashboard)
            contract = Stock(symbol, 'SMART', 'EUR')
            
            # Request 1-min bars (like dashboard)
            bars = ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr='1 D',
                barSizeSetting='1 min',
                whatToShow='TRADES',
                useRTH=False,
                formatDate=1
            )
            
            if bars and len(bars) > 0:
                bar = bars[-1]
                price = bar.close
                date = bar.date
                logger.info(f"[{i+1}] {symbol}: {price}€ @ {date}")
            else:
                logger.warning(f"[{i+1}] No bars available")
        
        except Exception as e:
            logger.error(f"[{i+1}] Error: {e}")
        
        # Wait 3 seconds between collections
        if i < 9:
            time.sleep(3)
    
    # Cleanup
    ib.disconnect()
    logger.info("Disconnected")

if __name__ == "__main__":
    test_live_price_loop()
