#!/usr/bin/env python
"""Module documentation."""

"""
Test script for IBKR connection, contract qualification, and order placement
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.order_manager import OrderManager
from backend.ibkr_collector import IBKRCollector
from backend.config import logger
from backend.models import Order, Ticker, SessionLocal
import time

def test_ibkr_connection():
    """Test IBKR connection"""
    logger.info("=" * 70)
    logger.info("TEST 1: IBKR Connection")
    logger.info("=" * 70)
    
    try:
        collector = IBKRCollector(client_id=1)
        
        logger.info("Attempting to connect...")
        if collector.connect():
            logger.info("✅ Connected to IBKR successfully!")
            logger.info(f"   Account: {collector.account}")
            logger.info(f"   Connected: {collector.connected}")
            return True, collector
        else:
            logger.error("❌ Failed to connect to IBKR")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ EXCEPTION during connection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

def test_contract_qualification():
    """Test contract qualification for TTE"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Contract Qualification (TTE)")
    logger.info("=" * 70)
    
    try:
        collector = IBKRCollector(client_id=1)
        
        if not collector.connect():
            logger.error("❌ Cannot test contracts - IBKR not connected")
            return False, None
        
        logger.info("Getting contract for TTE...")
        start = time.time()
        contract = collector.get_contract(symbol='TTE', exchange='SMART')
        elapsed = time.time() - start
        
        if contract:
            logger.info(f"✅ Contract qualified in {elapsed:.2f}s!")
            logger.info(f"   Symbol: {contract.symbol}")
            logger.info(f"   Exchange: {contract.exchange}")
            logger.info(f"   Currency: {contract.currency}")
            logger.info(f"   ConID: {contract.conId if hasattr(contract, 'conId') else 'N/A'}")
            collector.disconnect()
            return True, contract
        else:
            logger.error(f"❌ Could not qualify contract for TTE (took {elapsed:.2f}s)")
            collector.disconnect()
            return False, None
            
    except Exception as e:
        logger.error(f"❌ EXCEPTION during contract qualification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

def test_order_creation():
    """Test order creation and placement with IBKR connection"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Order Creation and Placement (BUY 1 TTE @ MARKET)")
    logger.info("=" * 70)
    
    try:
        # First, establish IBKR connection
        logger.info("Step 0: Connecting to IBKR...")
        collector = IBKRCollector(client_id=2)  # Use different client_id
        if not collector.connect():
            logger.warning("⚠️ IBKR Connection failed - will create order in PENDING status")
            collector = None
        else:
            logger.info(f"✅ IBKR Connected!")
        
        # Create OrderManager with IBKR collector
        om = OrderManager(ibkr_collector=collector)
        
        logger.info("\nStep 1: Creating order object...")
        order = om.create_order(
            symbol='TTE',
            action='BUY',
            quantity=1,
            order_type='MARKET'
        )
        
        if not order:
            logger.error("❌ FAILED: Order object not created")
            if collector:
                collector.disconnect()
            return False
        
        logger.info(f"✅ Order created!")
        logger.info(f"   Order ID: {order.id}")
        logger.info(f"   Status: {order.status}")
        logger.info(f"   Status Message: {order.status_message}")
        
        logger.info(f"\nStep 2: Checking order details...")
        logger.info(f"   Ticker ID: {order.ticker_id}")
        logger.info(f"   Action: {order.action}")
        logger.info(f"   Quantity: {order.quantity}")
        logger.info(f"   Type: {order.order_type}")
        logger.info(f"   IBKR Order ID: {order.ibkr_order_id or 'Not submitted'}")
        logger.info(f"   Perm Id: {order.perm_id or 'Not assigned'}")
        logger.info(f"   Submitted At: {order.submitted_at or 'Not submitted'}")
        
        logger.info("\nStep 3: Order Status Analysis...")
        if order.status.name == 'SUBMITTED':
            logger.info(f"✅ Order SUBMITTED to IBKR!")
            logger.info(f"   IBKR Order ID: {order.ibkr_order_id}")
            logger.info(f"   Waiting for execution status...")
            
            # Wait a bit to see if order gets filled
            time.sleep(2)
            
            # Refresh order from DB to check status
            db = SessionLocal()
            refreshed = db.query(Order).filter(Order.id == order.id).first()
            db.close()
            
            if refreshed:
                logger.info(f"   Updated Status: {refreshed.status.name}")
                logger.info(f"   Filled Qty: {refreshed.filled_quantity or 0}")
                logger.info(f"   Remaining Qty: {refreshed.remaining_quantity or 0}")
                if refreshed.avg_fill_price:
                    logger.info(f"   Avg Fill Price: {refreshed.avg_fill_price}")
            
            if collector:
                collector.disconnect()
            return True
        elif order.status.name == 'PENDING':
            logger.warning(f"⚠️ Order is PENDING (IBKR connection issue)")
            logger.info(f"   Message: {order.status_message}")
            logger.info(f"   Order will be submitted when IBKR connects")
            if collector:
                collector.disconnect()
            return True
        elif order.status.name == 'ERROR':
            logger.error(f"❌ Order has ERROR status")
            logger.error(f"   Message: {order.status_message}")
            if collector:
                collector.disconnect()
            return False
        else:
            logger.info(f"ℹ️ Order Status: {order.status.name}")
            if collector:
                collector.disconnect()
            return True
            
    except Exception as e:
        logger.error(f"❌ EXCEPTION during order creation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_order_retrieval():
    """Test retrieving the created order"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Order Retrieval from Database")
    logger.info("=" * 70)
    
    try:
        from backend.models import SessionLocal, Order
        from sqlalchemy import desc
        
        db = SessionLocal()
        
        logger.info("Retrieving last created order for TTE...")
        from backend.models import Ticker
        
        # Get TTE ticker
        tte_ticker = db.query(Ticker).filter(Ticker.symbol == 'TTE').first()
        if not tte_ticker:
            logger.error("❌ TTE ticker not found in database")
            db.close()
            return False
        
        # Find latest order for TTE
        latest_order = db.query(Order).filter(
            Order.ticker_id == tte_ticker.id
        ).order_by(desc(Order.created_at)).first()
        
        if latest_order:
            logger.info(f"✅ Order found in database!")
            logger.info(f"   Order ID: {latest_order.id}")
            logger.info(f"   Ticker ID: {latest_order.ticker_id}")
            logger.info(f"   Action: {latest_order.action}")
            logger.info(f"   Quantity: {latest_order.quantity}")
            logger.info(f"   Status: {latest_order.status.name}")
            logger.info(f"   Type: {latest_order.order_type}")
            logger.info(f"   Created: {latest_order.created_at}")
            logger.info(f"   IBKR Order ID: {latest_order.ibkr_order_id or 'N/A'}")
            
            if latest_order.status.name == 'SUBMITTED':
                logger.info(f"\n✅ Order successfully submitted to IBKR!")
            
            db.close()
            return True
        else:
            logger.warning("⚠️ No TTE order found in database")
            db.close()
            return False
            
    except Exception as e:
        logger.error(f"❌ EXCEPTION during order retrieval: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Run all tests"""
    logger.info("\n" + "🧪 " * 25)
    logger.info("BOURSICOTOR - IBKR & ORDER PLACEMENT TEST SUITE")
    logger.info("🧪 " * 25)
    
    results = {}
    
    # Test 1: Connection
    success, collector = test_ibkr_connection()
    results['Connection'] = success
    if collector:
        collector.disconnect()
    
    # Test 2: Contract
    success, contract = test_contract_qualification()
    results['Contract'] = success
    
    # Test 3: Order Creation
    success = test_order_creation()
    results['Order Creation'] = success
    
    # Test 4: Order Retrieval
    success = test_order_retrieval()
    results['Order Retrieval'] = success
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for s in results.values() if s)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    logger.info("=" * 70)
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
