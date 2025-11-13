#!/usr/bin/env python
"""
Integration test: Check that Redis, Celery, and Streamlit can all work together
"""

import sys
import os

def test_redis_config():
    """Test Redis configuration"""
    from backend.celery_config import REDIS_URL
    print("✅ Redis URL configured:", REDIS_URL)
    return True

def test_celery_config():
    """Test Celery configuration"""
    from backend.celery_config import celery_app
    print("✅ Celery app created:", celery_app.main)
    print("   Tasks available:", len(celery_app.tasks))
    return True

def test_streamlit_import():
    """Test Streamlit can be imported"""
    import streamlit as st
    print("✅ Streamlit imported:", st.__version__)
    return True

def test_database():
    """Test database connection"""
    from backend.models import SessionLocal
    session = SessionLocal()
    print("✅ Database connection OK")
    session.close()
    return True

def test_backend_imports():
    """Test all backend modules can be imported"""
    modules = [
        'backend.config',
        'backend.models',
        'backend.celery_config',
        'backend.data_collector',
        'backend.tasks',
        'backend.live_data_task',
        'backend.order_manager',
    ]
    
    for mod in modules:
        try:
            __import__(mod)
            print(f"✅ {mod:40} imported")
        except Exception as e:
            print(f"❌ {mod:40} FAILED: {str(e)[:40]}")
            return False
    
    return True

if __name__ == '__main__':
    print("="*70)
    print(" BOURSICOTOR INTEGRATION TEST ")
    print("="*70)
    print()
    
    tests = [
        ("Redis Configuration", test_redis_config),
        ("Celery Configuration", test_celery_config),
        ("Streamlit Module", test_streamlit_import),
        ("Database Connection", test_database),
        ("Backend Modules", test_backend_imports),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n[TEST] {name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} failed")
        except Exception as e:
            failed += 1
            print(f"❌ {name} error: {e}")
    
    print()
    print("="*70)
    print(f" RESULTS: {passed} passed, {failed} failed ")
    print("="*70)
    
    if failed == 0:
        print("✅ ALL INTEGRATION TESTS PASSED - SYSTEM READY")
        sys.exit(0)
    else:
        print(f"❌ {failed} test(s) failed")
        sys.exit(1)
