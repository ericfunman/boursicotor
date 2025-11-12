#!/usr/bin/env python
"""
Quick test to inspect what the trade object contains after placeOrder()
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.ibkr_collector import IBKRCollector

# Connect to IBKR
collector = IBKRCollector()
success = collector.connect()
if not success:
    print("❌ Failed to connect to IBKR")
    sys.exit(1)

print("✅ Connected to IBKR")

# Create an order for TTE
from ib_insync import Stock, Order

contract = Stock('TTE', 'SMART', 'EUR')
ib_order = Order()
ib_order.action = 'BUY'
ib_order.totalQuantity = 10
ib_order.orderType = 'MKT'

print(f"\nBefore placeOrder():")
print(f"  ib_order.orderId = {ib_order.orderId}")
print(f"  ib_order.permId = {ib_order.permId}")

# Place the order
trade = collector.ib.placeOrder(contract, ib_order)

print(f"\nAfter placeOrder():")
print(f"  ib_order.orderId = {ib_order.orderId}")
print(f"  ib_order.permId = {ib_order.permId}")
print(f"  trade object: {trade}")
print(f"  trade.order: {trade.order}")
print(f"  trade.order.orderId = {trade.order.orderId}")
print(f"  trade.order.permId = {trade.order.permId}")
print(f"  trade.orderStatus = {trade.orderStatus}")

# Check after a brief moment
import time
time.sleep(1)

print(f"\nAfter 1 second:")
print(f"  trade.order.orderId = {trade.order.orderId}")
print(f"  trade.orderStatus = {trade.orderStatus}")
print(f"  trade.orderStatus.orderId = {trade.orderStatus.orderId if trade.orderStatus else 'None'}")

print("\n✅ Test complete")
collector.disconnect()
