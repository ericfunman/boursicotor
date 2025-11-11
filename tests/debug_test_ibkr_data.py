#!/usr/bin/env python3
"""Module documentation."""

"""
Test script to check IBKR data format
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ibkr_collector import IBKRCollector
import pandas as pd

def test_ibkr_data_format():
    """Test IBKR data collection and inspect the DataFrame format"""
    print("Testing IBKR data collection...")

    collector = IBKRCollector()

    # Try to collect a small amount of data
    try:
        print("Connecting to IBKR...")
        if not collector.connect():
            print("Failed to connect to IBKR")
            return

        print("Collecting sample data for WLN...")
        df = collector.get_historical_data_chunked(
            symbol='WLN',
            duration='1 D',  # Just 1 day for testing
            bar_size='1 min',
            progress_callback=lambda current, total: print(f"Progress: {current}/{total}")
        )

        if df is None or df.empty:
            print("No data received from IBKR")
            return

        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"Data types:\n{df.dtypes}")
        print(f"First 5 rows:\n{df.head()}")
        print(f"Last 5 rows:\n{df.tail()}")

        # Check for NaN values
        nan_counts = df.isnull().sum()
        print(f"NaN counts:\n{nan_counts}")

        # Check data ranges
        print(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Open range: {df['open'].min()} to {df['open'].max()}")
        print(f"Volume range: {df['volume'].min()} to {df['volume'].max()}")

        # Test save_to_database with just first 10 rows
        print("\nTesting save_to_database with first 10 rows...")
        test_df = df.head(10).copy()
        result = collector.save_to_database('WLN_TEST', test_df, '1min', 'Worldline Test')
        print(f"Save result: {result}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if collector.connected:
            collector.disconnect()

if __name__ == "__main__":
    test_ibkr_data_format()