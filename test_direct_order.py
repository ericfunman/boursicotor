#!/usr/bin/env python
"""
Direct test of IBKR order execution - bypassing OrderManager
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger
from ib_insync import Stock, MarketOrder
import time

def test_direct_order():
    """Test placing order directly with IBKR"""
    logger.info("=" * 70)
    logger.info("DIRECT IBKR TEST - Place order without OrderManager")
    logger.info("=" * 70)
    
    try:
        # Connect to IBKR
        logger.info("\nStep 1: Connecting to IBKR...")
        collector = IBKRCollector(client_id=4)
        if not collector.connect():
            logger.error("❌ Connection failed")
            return False
        
        logger.info(f"✅ Connected! Account: {collector.account}")
        
        # Create contract
        logger.info("\nStep 2: Creating contract...")
        contract = collector.get_contract('TTE', exchange='SMART')
        if not contract:
            logger.error("❌ Cannot get contract")
            collector.disconnect()
            return False
        
        logger.info(f"✅ Contract: {contract.symbol} on {contract.exchange} ({contract.currency})")
        
        # Place order
        logger.info("\nStep 3: Placing order (BUY 10 TTE @ MARKET)...")
        order = MarketOrder('BUY', 10)
        trade = collector.ib.placeOrder(contract, order)
        logger.info(f"✅ Order placed, IBKR Order ID: {trade.order.orderId}")
        logger.info(f"   Initial status: {trade.orderStatus.status}")
        logger.info(f"   Filled: {trade.orderStatus.filled}, Remaining: {trade.orderStatus.remaining}")
        
        # Monitor order
        logger.info("\nStep 4: Monitoring order execution (30 seconds)...")
        start = time.time()
        last_status = trade.orderStatus.status
        
        while time.time() - start < 30:
            # Use waitOnUpdate to wait for events
            collector.ib.waitOnUpdate(timeout=1)
            
            # Check status
            status = trade.orderStatus.status
            filled = trade.orderStatus.filled
            remaining = trade.orderStatus.remaining
            avg_price = trade.orderStatus.avgFillPrice
            
            # Log if changed
            if status != last_status or filled > 0:
                elapsed = int(time.time() - start)
                logger.info(f"   [{elapsed}s] Status: {status} | Filled: {filled}/10 | Remaining: {remaining} | Avg: {avg_price:.2f}")
                last_status = status
            
            # Check if filled
            if int(filled) >= 10:
                logger.info(f"\n✅ ORDER FILLED!")
                logger.info(f"   Final status: {status}")
                logger.info(f"   Filled: {filled}")
                logger.info(f"   Avg price: {avg_price:.2f}")
                collector.disconnect()
                return True
        
        # Timeout
        logger.warning(f"\n⏱️ Timeout - order NOT filled")
        logger.warning(f"   Final status: {trade.orderStatus.status}")
        logger.warning(f"   Filled: {trade.orderStatus.filled}/10")
        logger.warning(f"   Remaining: {trade.orderStatus.remaining}")
        
        collector.disconnect()
        return False
        
    except Exception as e:
        logger.error(f"❌ EXCEPTION: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_direct_order()
    sys.exit(0 if success else 1)
