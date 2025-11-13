#!/usr/bin/env python
"""Test live price collection in detail"""

from backend.live_price_thread import start_live_price_collection, is_collecting, stop_live_price_collection
import time

print("Starting collection for TTE...")
start_live_price_collection('TTE', interval=2)

print("Waiting 8 seconds to see price collection...")
for i in range(4):
    time.sleep(2)
    print(f"  [{i*2+2}s] is_collecting={is_collecting('TTE')}")

print("\nStopping collection...")
stop_live_price_collection()
print("Done")
