#!/usr/bin/env python3
"""Module documentation."""

"""
Debug script to test data saving with real IBKR data for longer periods
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ibkr_collector import IBKRCollector
import pandas as pd

def test_ibkr_data_saving():
    """Test IBKR data collection and saving for longer periods"""
    print("Testing IBKR data collection and saving...")

    collector = IBKRCollector()

    # Try to collect data for a longer period
    try:
        print("Connecting to IBKR...")
        if not collector.connect():
            print("Failed to connect to IBKR")
            return

        print("Collecting sample data for WLN (longer period)...")
        # Try 3 months instead of 1 day
        df = collector.get_historical_data_chunked(
            symbol='WLN',
            duration='3 M',  # Longer period
            bar_size='1 min',
            progress_callback=lambda current, total: print(f"Collection progress: {current}/{total}")
        )

        if df is None or df.empty:
            print("No data received from IBKR")
            return

        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"Data types:\n{df.dtypes}")

        # Check for issues in the data
        print(f"NaN counts:\n{df.isnull().sum()}")

        # Check timestamp range
        print(f"Timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        # Check for duplicate timestamps
        duplicates = df['timestamp'].duplicated().sum()
        print(f"Duplicate timestamps: {duplicates}")

        # Check volume data type and range
        print(f"Volume data type: {df['volume'].dtype}")
        print(f"Volume range: {df['volume'].min()} to {df['volume'].max()}")
        print(f"Volume unique values count: {df['volume'].nunique()}")

        # Test saving a subset first
        print("\nTesting save_to_database with first 1000 rows...")
        test_df = df.head(1000).copy()
        result = collector.save_to_database('WLN_DEBUG', test_df, '1min', 'Worldline Debug')
        print(f"Save result for 1000 rows: {result}")

        # Test saving all data
        print(f"\nTesting save_to_database with all {len(df)} rows...")
        result = collector.save_to_database('WLN_DEBUG2', df, '1min', 'Worldline Debug Full')
        print(f"Save result for all rows: {result}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if collector.connected:
            collector.disconnect()

if __name__ == "__main__":
    test_ibkr_data_saving()