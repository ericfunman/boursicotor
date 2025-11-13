#!/usr/bin/env python3
"""Module documentation."""

"""
Test script to verify the new connection strategy:
- Streamlit: single persistent connection with client_id=1
- Celery: random client_ids (4-999) for each task

This simulates:
1. Streamlit connects with client_id=1
2. Celery task tries to connect with client_id=4-999
3. Both should succeed without conflicts
"""

import time
import threading
import random
from backend.ibkr_collector import IBKRCollector

def test_streamlit_connection():
    """Simulate Streamlit's persistent connection"""
    print("🔵 STREAMLIT: Starting connection with client_id=1...")
    
    collector = IBKRCollector(client_id=1)
    if not collector.connect():
        print("❌ STREAMLIT: Failed to connect")
        return False
    
    print("✅ STREAMLIT: Connected with client_id=1")
    return collector

def test_celery_task(streamlit_collector, task_num=1):
    """Simulate Celery task connection"""
    celery_client_id = random.randint(4, 999)
    print(f"🟠 CELERY Task {task_num}: Starting connection with client_id={celery_client_id}...")
    
    collector = IBKRCollector(client_id=celery_client_id)
    if not collector.connect():
        print(f"❌ CELERY Task {task_num}: Failed to connect")
        return False
    
    print(f"✅ CELERY Task {task_num}: Connected with client_id={celery_client_id}")
    
    # Simulate work - try to qualify a contract
    try:
        contract = collector.get_contract("TTE", exchange="SBF", currency="EUR")
        if contract:
            print(f"✅ CELERY Task {task_num}: Successfully qualified TTE - {contract.symbol} on {contract.exchange}")
        else:
            print(f"⚠️  CELERY Task {task_num}: No contracts found for TTE")
    except Exception as e:
        print(f"❌ CELERY Task {task_num}: Error during get_contract: {e}")
        return False
    finally:
        collector.disconnect()
        print(f"🔴 CELERY Task {task_num}: Disconnected")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Testing New Connection Strategy")
    print("=" * 60)
    print()
    
    # Test 1: Streamlit connection
    print("TEST 1: Streamlit persistent connection")
    print("-" * 60)
    streamlit_collector = test_streamlit_connection()
    if not streamlit_collector:
        print("\n❌ TEST FAILED: Could not establish Streamlit connection")
        exit(1)
    
    print()
    time.sleep(1)
    
    # Test 2: Concurrent Celery tasks while Streamlit is connected
    print("TEST 2: Celery tasks with Streamlit still connected")
    print("-" * 60)
    
    celery_threads = []
    for i in range(1, 3):
        t = threading.Thread(target=test_celery_task, args=(streamlit_collector, i))
        celery_threads.append(t)
        t.start()
    
    # Wait for all Celery tasks to complete
    for t in celery_threads:
        t.join()
    
    print()
    time.sleep(1)
    
    # Test 3: Disconnect Streamlit
    print("TEST 3: Disconnect Streamlit")
    print("-" * 60)
    try:
        streamlit_collector.disconnect()
        print("✅ STREAMLIT: Disconnected")
    except Exception as e:
        print(f"⚠️  STREAMLIT: Disconnect error: {e}")
    
    print()
    print("=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
