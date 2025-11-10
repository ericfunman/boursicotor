#!/usr/bin/env python
"""Module documentation."""

"""
Diagnostic: Check fills structure to understand how to match orderId
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.ibkr_collector import IBKRCollector
from backend.config import logger

try:
    # Connect
    collector = IBKRCollector(client_id=5)
    if not collector.connect():
        logger.error("Connection failed")
        sys.exit(1)
    
    logger.info(f"Connected to {collector.account}")
    
    # Get fills
    fills = collector.ib.fills()
    logger.info(f"\nFound {len(fills)} fills")
    
    if fills:
        f = fills[0]
        logger.info(f"\nFirst fill object: {f}")
        logger.info(f"  Type: {type(f)}")
        logger.info(f"  Dir: {dir(f)}")
        
        if hasattr(f, 'execution'):
            logger.info(f"\n  execution: {f.execution}")
            logger.info(f"    type: {type(f.execution)}")
            logger.info(f"    dir: {dir(f.execution)}")
            if hasattr(f.execution, 'orderId'):
                logger.info(f"    orderId: {f.execution.orderId}")
            if hasattr(f.execution, 'execId'):
                logger.info(f"    execId: {f.execution.execId}")
        
        if hasattr(f, 'order'):
            logger.info(f"\n  order: {f.order}")
            if hasattr(f.order, 'orderId'):
                logger.info(f"    orderId: {f.order.orderId}")
        
        if hasattr(f, 'contract'):
            logger.info(f"\n  contract: {f.contract}")
            if hasattr(f.contract, 'symbol'):
                logger.info(f"    symbol: {f.contract.symbol}")
    
    collector.disconnect()
    
except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    logger.error(traceback.format_exc())
