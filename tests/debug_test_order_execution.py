#!/usr/bin/env python
"""Module documentation."""

"""
Test script to verify order execution (SUBMITTED → FILLED)
Test orders for TTE (50 shares) and WLN (1 share)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.order_manager import OrderManager
from backend.ibkr_collector import IBKRCollector
from backend.config import logger
from backend.models import Order, SessionLocal
import time

def test_single_order(collector, om, symbol, quantity):
    """Test a single order"""
    logger.info(f"\n{'='*70}")
    logger.info(f"Testing: BUY {quantity} {symbol} @ MARKET")
    logger.info(f"{'='*70}")
    
    # Create and submit order
    logger.info(f"\nStep 1: Creating order (BUY {quantity} {symbol} @ MARKET)...")
    
    order = om.create_order(
        symbol=symbol,
        action='BUY',
        quantity=quantity,
        order_type='MARKET'
    )
    
    if not order:
        logger.error(f"❌ Order creation failed for {symbol}")
        return False
    
    logger.info(f"✅ Order created: ID={order.id}, IBKR_ID={order.ibkr_order_id}, Status={order.status.name}")
    
    # Wait for execution
    logger.info(f"\nStep 2: Waiting for order execution (max 30 seconds)...")
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
                logger.info(f"   [{elapsed}s] Status: {current_status} | Filled: {filled}/{quantity} | Remaining: {remaining} | Avg: {avg_price:.2f}")
                last_status = current_status
            
            # Check if order is filled
            if current_status == 'FILLED' and filled == quantity:
                logger.info(f"\n✅ ORDER FULLY FILLED!")
                logger.info(f"   Final Status: {current_status}")
                logger.info(f"   Filled Quantity: {filled}")
                logger.info(f"   Avg Fill Price: {avg_price:.2f}")
                return True
            
            # Check if partially filled
            if filled > 0 and current_status != 'FILLED':
                logger.info(f"   ⏳ Partially filled: {filled}/{quantity}")
    
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
        logger.warning(f"   Filled: {final_order.filled_quantity or 0}/{quantity}")
        logger.warning(f"   IBKR Order ID: {final_order.ibkr_order_id}")
    
    return False

def test_order_execution():
    """Test complete order lifecycle for multiple tickers"""
    logger.info("=" * 70)
    logger.info("TEST: Order Execution Verification - Multiple Tickers")
    logger.info("=" * 70)
    
    try:
        # Connect to IBKR
        logger.info("\nConnecting to IBKR...")
        collector = IBKRCollector(client_id=3)
        if not collector.connect():
            logger.error("❌ IBKR Connection failed")
            return False
        
        logger.info(f"✅ Connected! Account: {collector.account}")
        
        # Create OrderManager
        om = OrderManager(ibkr_collector=collector)
        
        # Test orders for different tickers
        test_cases = [
            ('TTE', 50),   # TotalEnergies - 50 shares
            ('WLN', 1),    # Walnur - 1 share
        ]
        
        results = {}
        for symbol, quantity in test_cases:
            success = test_single_order(collector, om, symbol, quantity)
            results[symbol] = success
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("SUMMARY OF RESULTS")
        logger.info("=" * 70)
        
        for symbol, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"  {symbol}: {status}")
        
        # Check IBKR portfolio
        logger.info("\nStep 3: Checking IBKR Portfolio...")
        try:
            positions = collector.ib.positions()
            if positions:
                logger.info(f"✅ Found {len(positions)} positions:")
                for pos in positions:
                    logger.info(f"   {pos.contract.symbol}: {pos.position} shares @ {pos.avgCost:.2f}")
            else:
                logger.warning(f"❌ No positions found in IBKR")
        except Exception as e:
            logger.error(f"❌ Could not get positions: {e}")
        
        collector.disconnect()
        
        # Return True if all tests passed
        return all(results.values())
        
    except Exception as e:
        logger.error(f"❌ EXCEPTION: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("\n" + "🧪 " * 25)
    logger.info("ORDER EXECUTION TEST - VERIFY ORDERS ARE FILLED")
    logger.info("🧪 " * 25)
    
    success = test_order_execution()
    
    logger.info("\n" + "=" * 70)
    if success:
        logger.info("✅ ALL TESTS PASSED - All orders were fully executed")
    else:
        logger.warning("❌ SOME TESTS FAILED - Orders were NOT fully executed")
        logger.warning("   Possible causes:")
        logger.warning("   1. Market conditions (no liquidity)")
        logger.warning("   2. IBKR order rejection")
        logger.warning("   3. Connection issue during execution")
        logger.warning("   4. Order stuck in SUBMITTED state")
    logger.info("=" * 70)
    
    sys.exit(0 if success else 1)
