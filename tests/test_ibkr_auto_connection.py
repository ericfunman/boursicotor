#!/usr/bin/env python3
"""Module documentation."""

"""
Test script to verify IBKR auto-connection functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ibkr_auto_connection():
    """Test the IBKR auto-connection functionality"""
    try:
        # Import the connection functions
        from frontend.app import init_global_ibkr_connection, connect_global_ibkr, get_global_ibkr

        print("🔍 Testing IBKR auto-connection...")

        # Initialize connection
        init_global_ibkr_connection()
        print("✅ Global connection initialized")

        # Check initial state
        initial_connected = get_global_ibkr() is not None
        print(f"📊 Initial connection state: {'Connected' if initial_connected else 'Not connected'}")

        # Attempt connection
        print("🔌 Attempting to connect to IBKR...")
        success, message = connect_global_ibkr()

        if success:
            print(f"✅ Connection successful: {message}")
            collector = get_global_ibkr()
            if collector:
                print("✅ Global IBKR collector is available")
                return True
            else:
                print("❌ Global IBKR collector is None after successful connection")
                return False
        else:
            print(f"❌ Connection failed: {message}")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ibkr_auto_connection()
    print(f"\n{'✅ All tests passed!' if success else '❌ Tests failed!'}")
    sys.exit(0 if success else 1)