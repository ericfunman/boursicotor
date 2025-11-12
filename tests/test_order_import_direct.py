#!/usr/bin/env python3
"""Module documentation."""

"""Test script to check Order import"""

try:
    from backend.models import Order
    print("✅ Order import successful")
    print(f"Order class: {Order}")
    print(f"Order table: {Order.__tablename__}")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")