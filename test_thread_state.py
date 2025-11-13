#!/usr/bin/env python
"""Test live price collection state"""

from backend.live_price_thread import (
    start_live_price_collection, 
    is_collecting, 
    get_current_symbol,
    stop_live_price_collection
)
import time

print("Initial state:")
print(f"  is_collecting('TTE'): {is_collecting('TTE')}")
print(f"  get_current_symbol(): {get_current_symbol()}")

print("\nStarting collection for TTE...")
result = start_live_price_collection('TTE', interval=1)
print(f"  start_live_price_collection returned: {result}")

time.sleep(0.5)

print("\nAfter start:")
print(f"  is_collecting('TTE'): {is_collecting('TTE')}")
print(f"  get_current_symbol(): {get_current_symbol()}")

print("\nStopping collection...")
result = stop_live_price_collection()
print(f"  stop_live_price_collection returned: {result}")

time.sleep(0.5)

print("\nAfter stop:")
print(f"  is_collecting('TTE'): {is_collecting('TTE')}")
print(f"  get_current_symbol(): {get_current_symbol()}")
