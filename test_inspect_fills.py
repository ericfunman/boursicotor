#!/usr/bin/env python
"""
Debug: Inspect fill objects to understand their structure
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger

try:
    collector = IBKRCollector(client_id=7)
    if not collector.connect():
        logger.error("Connection failed")
        sys.exit(1)
    
    logger.info(f"Connected to {collector.account}")
    
    # Get fills
    fills = collector.ib.fills()
    logger.info(f"\nFound {len(fills)} fills total")
    
    # Filter for TTE
    tte_fills = [f for f in fills if f.contract.symbol == 'TTE']
    logger.info(f"TTE fills: {len(tte_fills)}")
    
    if tte_fills:
        logger.info(f"\nTTE fill orderId values:")
        for f in tte_fills[-5:]:  # Last 5
            logger.info(f"  orderId={f.execution.orderId}, shares={f.execution.shares}, price={f.execution.price}, time={f.execution.time}")
    
    collector.disconnect()
    
except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    logger.error(traceback.format_exc())
