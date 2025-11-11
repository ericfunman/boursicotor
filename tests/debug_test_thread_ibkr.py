"""Test IBKR access from thread"""
import threading
import time
from backend.ibkr_collector import IBKRCollector
from backend.config import logger

def test_in_thread(ibkr):
    """Test function that runs in thread"""
    try:
        logger.info(f"[Thread] Started")
        logger.info(f"[Thread] IBKR object: {ibkr}")
        logger.info(f"[Thread] IBKR connected: {ibkr.ib.isConnected()}")
        
        from ib_insync import Stock
        contract = Stock('WLN', 'SMART', 'EUR')
        logger.info(f"[Thread] Contract created: {contract}")
        
        logger.info(f"[Thread] Calling qualifyContracts...")
        qualified = ibkr.ib.qualifyContracts(contract)
        logger.info(f"[Thread] qualifyContracts returned: {qualified}")
        
        if qualified:
            logger.info(f"[Thread] SUCCESS! Contract: {qualified[0]}")
        else:
            logger.error(f"[Thread] Failed to qualify contract")
            
    except Exception as e:
        logger.error(f"[Thread] EXCEPTION: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Main
logger.info("=== Starting IBKR Thread Test ===")

ibkr = IBKRCollector()
logger.info(f"Main: IBKR created, connected: {ibkr.ib.isConnected()}")

logger.info("Main: Starting thread...")
thread = threading.Thread(target=test_in_thread, args=(ibkr,))
thread.start()

logger.info("Main: Waiting for thread...")
thread.join(timeout=10)

if thread.is_alive():
    logger.error("Main: Thread is still alive after 10s - BLOCKED!")
else:
    logger.info("Main: Thread completed successfully")

logger.info("=== Test Complete ===")
