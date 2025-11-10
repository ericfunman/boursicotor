#!/usr/bin/env python
"""
Test script to verify order execution (SUBMITTED → FILLED)
and check IBKR portfolio
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.order_manager import OrderManager
from backend.ibkr_collector import IBKRCollector
from backend.config import logger
from backend.models import Order, SessionLocal
import time

def test_order_execution():
    """Test complete order lifecycle: submit → wait → check fills"""
    logger.info("=" * 70)
    logger.info("TEST: Order Execution Verification")
    logger.info("=" * 70)
    
    try:
        # Connect to IBKR
        logger.info("\nStep 1: Connecting to IBKR...")
        collector = IBKRCollector(client_id=3)
        if not collector.connect():
            logger.error("❌ IBKR Connection failed")
            return False
        
        logger.info(f"✅ Connected! Account: {collector.account}")
        
        # Create and submit order
        logger.info("\nStep 2: Creating order (BUY 50 TTE @ MARKET)...")
        om = OrderManager(ibkr_collector=collector)
        
        order = om.create_order(
            symbol='TTE',
            action='BUY',
            quantity=50,
            order_type='MARKET'
        )
        
        if not order:
            logger.error("❌ Order creation failed")
            collector.disconnect()
            return False
        
        logger.info(f"✅ Order created: ID={order.id}, IBKR_ID={order.ibkr_order_id}, Status={order.status.name}")
        
        # Wait for execution
        logger.info("\nStep 3: Waiting for order execution (max 30 seconds)...")
        start_time = time.time()
        last_status = order.status.name
        
        while time.time() - start_time < 30:
            time.sleep(1)
            
            # Refresh from DB
            db = SessionLocal()
            refreshed = db.query(Order).filter(Order.id == order.id).first()
            db.close()
            
            if refreshed:
                current_status = refreshed.status.name
                filled = refreshed.filled_quantity or 0
                remaining = refreshed.remaining_quantity or 0
                avg_price = refreshed.avg_fill_price or 0
                
                # Log status changes
                if current_status != last_status or filled > 0:
                    elapsed = int(time.time() - start_time)
                    logger.info(f"   [{elapsed}s] Status: {current_status} | Filled: {filled}/50 | Remaining: {remaining} | Avg: {avg_price:.2f}")
                    last_status = current_status
                
                # Check if order is filled
                if current_status == 'FILLED' and filled == 50:
                    logger.info(f"\n✅ ORDER FULLY FILLED!")
                    logger.info(f"   Final Status: {current_status}")
                    logger.info(f"   Filled Quantity: {filled}")
                    logger.info(f"   Avg Fill Price: {avg_price:.2f}")
                    logger.info(f"   Commission: {refreshed.commission:.2f}")
                    return True
                
                # Check if partially filled
                if filled > 0 and current_status != 'FILLED':
                    logger.info(f"   ⏳ Partially filled: {filled}/50")
        
        # After timeout, check final status
        logger.info(f"\n⏱️ Timeout reached (30s)")
        
        # Wait a bit more for background thread to finish
        time.sleep(3)
        
        db = SessionLocal()
        final_order = db.query(Order).filter(Order.id == order.id).first()
        db.close()
        
        if final_order:
            logger.warning(f"❌ Order NOT fully filled")
            logger.warning(f"   Final Status: {final_order.status.name}")
            logger.warning(f"   Filled: {final_order.filled_quantity or 0}/50")
            logger.warning(f"   Remaining: {final_order.remaining_quantity or 0}")
            logger.warning(f"   IBKR Order ID: {final_order.ibkr_order_id}")
        
        # Check IBKR portfolio
        logger.info("\nStep 4: Checking IBKR Portfolio...")
        try:
            positions = collector.ib.positions()
            if positions:
                logger.info(f"✅ Found {len(positions)} positions:")
                for pos in positions:
                    logger.info(f"   {pos.contract.symbol}: {pos.position} shares @ {pos.avgCost:.2f}")
                    if pos.contract.symbol == 'TTE':
                        logger.info(f"   ✅ TTE position found: {pos.position} shares")
            else:
                logger.warning(f"❌ No positions found in IBKR")
        except Exception as e:
            logger.error(f"❌ Could not get positions: {e}")
        
        # Check fills
        logger.info("\nStep 5: Checking IBKR Fills/Trades...")
        try:
            fills = collector.ib.fills()
            if fills:
                logger.info(f"✅ Found {len(fills)} fills:")
                tte_fills = [f for f in fills if f.contract.symbol == 'TTE']
                if tte_fills:
                    logger.info(f"   TTE fills: {len(tte_fills)}")
                    for fill in tte_fills[-3:]:  # Last 3 fills
                        logger.info(f"   - {fill.execution.time}: {fill.execution.side} {fill.execution.shares} @ {fill.execution.price}")
                else:
                    logger.warning(f"❌ No TTE fills found")
            else:
                logger.warning(f"❌ No fills found")
        except Exception as e:
            logger.error(f"❌ Could not get fills: {e}")
        
        collector.disconnect()
        return False
        
    except Exception as e:
        logger.error(f"❌ EXCEPTION: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("\n" + "🧪 " * 25)
    logger.info("ORDER EXECUTION TEST - VERIFY BUY ORDER IS FILLED")
    logger.info("🧪 " * 25)
    
    success = test_order_execution()
    
    logger.info("\n" + "=" * 70)
    if success:
        logger.info("✅ TEST PASSED - Order was fully executed")
    else:
        logger.warning("❌ TEST FAILED - Order was NOT fully executed")
        logger.warning("   Possible causes:")
        logger.warning("   1. Market conditions (no liquidity)")
        logger.warning("   2. IBKR order rejection")
        logger.warning("   3. Connection issue during execution")
        logger.warning("   4. Order stuck in SUBMITTED state")
    logger.info("=" * 70)
    
    sys.exit(0 if success else 1)
