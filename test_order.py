#!/usr/bin/env python
"""
Test script for order placement
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.order_manager import OrderManager
from backend.config import logger

def test_place_order():
    """Test placing a simple order"""
    logger.info("=" * 60)
    logger.info("TEST: Placing order for 1 TTE @ MARKET")
    logger.info("=" * 60)
    
    try:
        om = OrderManager()
        
        # Test order creation
        logger.info("Creating order...")
        order = om.create_order(
            symbol='TTE',
            action='BUY',
            quantity=1,
            order_type='MARKET'
        )
        
        if order:
            logger.info(f"✅ SUCCESS: Order created!")
            logger.info(f"   Order ID: {order.id}")
            logger.info(f"   Status: {order.status}")
            logger.info(f"   IBKR Order ID: {order.ibkr_order_id}")
            logger.info(f"   Message: {order.status_message}")
            return True
        else:
            logger.error("❌ FAILED: Order not created")
            return False
            
    except Exception as e:
        logger.error(f"❌ EXCEPTION: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_place_order()
    sys.exit(0 if success else 1)
