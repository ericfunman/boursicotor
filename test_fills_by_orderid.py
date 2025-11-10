#!/usr/bin/env python
"""
Debug: Check fills for specific orderId
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger

try:
    collector = IBKRCollector(client_id=6)
    if not collector.connect():
        logger.error("Connection failed")
        sys.exit(1)
    
    logger.info(f"Connected to {collector.account}")
    
    # Get fills
    fills = collector.ib.fills()
    logger.info(f"\nFound {len(fills)} fills")
    
    # Group by orderId
    by_order_id = {}
    for f in fills:
        oid = f.execution.orderId
        if oid not in by_order_id:
            by_order_id[oid] = []
        by_order_id[oid].append(f)
    
    logger.info(f"\nFills by orderId:")
    for oid in sorted(by_order_id.keys(), reverse=True)[:10]:  # Last 10
        fills_for_order = by_order_id[oid]
        symbol = fills_for_order[0].contract.symbol
        shares = sum(f.execution.shares for f in fills_for_order)
        logger.info(f"  Order {oid} ({symbol}): {shares} shares in {len(fills_for_order)} fills")
        for f in fills_for_order:
            logger.info(f"    - {f.execution.time}: {f.execution.shares} @ {f.execution.price}")
    
    collector.disconnect()
    
except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    logger.error(traceback.format_exc())
