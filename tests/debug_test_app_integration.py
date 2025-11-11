#!/usr/bin/env python
"""Module documentation."""

"""
Integration test for the complete application
Tests order execution through OrderManager (like the Streamlit UI would)
"""
import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.config import logger
from backend.ibkr_collector import IBKRCollector
from backend.order_manager import OrderManager
from backend.database import SessionLocal
from backend.models import Order, OrderStatus
from datetime import datetime

def test_app_integration():
    """Test complete order flow through the app"""
    
    logger.info("\n" + "="*70)
    logger.info("APPLICATION INTEGRATION TEST - FULL ORDER FLOW")
    logger.info("="*70)
    
    try:
        # Step 1: Connect to IBKR
        logger.info("\nStep 1: Connecting to IBKR...")
        collector = IBKRCollector()
        if not collector.connect():
            logger.error("❌ Failed to connect to IBKR")
            return False
        logger.info("✅ Connected to IBKR")
        account = collector.ib.wrapper.accountValues
        logger.info(f"   Account: {collector.ib.managedAccounts()}")
        
        # Step 2: Create OrderManager
        logger.info("\nStep 2: Creating OrderManager...")
        om = OrderManager(collector)
        logger.info("✅ OrderManager created")
        
        # Step 3: Create and place order
        logger.info("\nStep 3: Creating BUY order (50 TTE @ MARKET)...")
        order = om.create_order(
            ticker_symbol='TTE',
            quantity=50,
            order_type='MARKET',
            action='BUY',
            time_in_force='DAY'
        )
        
        if not order:
            logger.error("❌ Failed to create order")
            collector.disconnect()
            return False
        
        logger.info(f"✅ Order created: ID={order.id}, IBKR_ID={order.ibkr_order_id}, Status={order.status.name}")
        
        # Step 4: Wait for execution
        logger.info("\nStep 4: Waiting for order execution (max 30 seconds)...")
        start_time = time.time()
        check_interval = 1  # Check every 1 second
        
        while time.time() - start_time < 30:
            time.sleep(check_interval)
            
            # Refresh from DB
            db = SessionLocal()
            refreshed = db.query(Order).filter(Order.id == order.id).first()
            db.close()
            
            if refreshed:
                elapsed = int(time.time() - start_time)
                filled = refreshed.filled_quantity or 0
                status = refreshed.status.name
                
                if filled > 0 or status == 'FILLED':
                    logger.info(f"   [{elapsed}s] Status: {status} | Filled: {filled}/50")
                
                if status == 'FILLED' and filled >= 50:
                    logger.info("\n✅ ORDER FULLY FILLED!")
                    logger.info(f"   Final Status: {status}")
                    logger.info(f"   Filled: {filled}")
                    logger.info(f"   Avg Price: {refreshed.avg_fill_price:.2f}")
                    collector.disconnect()
                    return True
        
        # Timeout reached
        logger.warning(f"\n⏱️ Timeout reached (30s)")
        
        # Check final status
        db = SessionLocal()
        final_order = db.query(Order).filter(Order.id == order.id).first()
        db.close()
        
        if final_order:
            filled = final_order.filled_quantity or 0
            logger.warning(f"❌ Order NOT fully filled")
            logger.warning(f"   Final Status: {final_order.status.name}")
            logger.warning(f"   Filled: {filled}/50")
            
            # But verify in IBKR
            logger.info("\nStep 5: Verifying in IBKR...")
            positions = collector.ib.positions()
            for pos in positions:
                if pos.contract.symbol == 'TTE':
                    logger.info(f"✅ IBKR shows: {pos.position} shares of TTE")
            
            fills = collector.ib.fills()
            tte_fills = [f for f in fills if f.contract.symbol == 'TTE']
            logger.info(f"✅ IBKR shows: {len(tte_fills)} TTE fills total")
        
        collector.disconnect()
        return False
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_app_integration()
    
    if success:
        logger.info("\n" + "="*70)
        logger.info("✅ APP INTEGRATION TEST PASSED")
        logger.info("="*70)
        sys.exit(0)
    else:
        logger.info("\n" + "="*70)
        logger.info("❌ APP INTEGRATION TEST FAILED")
        logger.info("="*70)
        sys.exit(1)
