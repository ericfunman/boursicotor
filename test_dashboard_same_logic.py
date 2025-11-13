"""
Test: Use EXACT same logic as dashboard to fetch TTE price
"""
import time as time_module
from ib_insync import IB, Stock
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_tte_price_like_dashboard():
    """Fetch TTE price using EXACT same logic as dashboard"""
    
    print("\n" + "="*80)
    print("FETCHING TTE PRICE - SAME LOGIC AS DASHBOARD")
    print("="*80 + "\n")
    
    # Create temporary connection with clientId=50 (EXACTLY like dashboard)
    ib_market = IB()
    
    try:
        logger.info("Connecting with clientId=50 (SAME AS DASHBOARD)")
        # Try port 4002 (gateway) or 7497 (TWS)
        ib_market.connect('127.0.0.1', 4002, clientId=50)
        
        # Wait for connection
        for i in range(5):
            time_module.sleep(0.5)
            if ib_market.isConnected():
                logger.info(f"✅ Connected after {(i+1)*0.5}s")
                break
        
        if not ib_market.isConnected():
            logger.error("❌ Failed to connect to IBKR!")
            return None
        
        # Create contract EXACTLY like dashboard
        symbol = 'TTE'
        logger.info(f"Creating contract for {symbol}")
        contract = Stock(symbol, 'SMART', 'EUR')
        logger.info(f"Contract: {contract}")
        
        # Request historical data EXACTLY like dashboard
        logger.info("Requesting historical data: '1 D', '1 day'")
        bars = ib_market.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='1 D',           # SAME as dashboard
            barSizeSetting='1 day',      # SAME as dashboard
            whatToShow='TRADES',
            useRTH=False,
            formatDate=1
        )
        
        logger.info(f"✅ Got {len(bars)} bars")
        
        if bars and len(bars) > 0:
            bar = bars[-1]
            price = bar.close
            logger.info(f"✅ LAST BAR: date={bar.date}, close={price}€")
            print(f"\n{'='*80}")
            print(f"🎯 SUCCESS! TTE price = {price}€")
            print(f"{'='*80}\n")
            return price
        else:
            logger.warning("❌ No bars returned!")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return None
    finally:
        try:
            ib_market.disconnect()
            logger.info("Disconnected")
        except:
            pass

if __name__ == '__main__':
    price = fetch_tte_price_like_dashboard()
    if price:
        print(f"\n✅ Final result: TTE = {price}€\n")
    else:
        print(f"\n❌ Failed to fetch price\n")
