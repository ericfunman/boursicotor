#!/usr/bin/env python3
"""Module documentation."""

"""
Test script to debug data saving issue
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
from backend.ibkr_collector import IBKRCollector
from backend.models import SessionLocal, HistoricalData, Ticker

def test_save_to_database():
    """Test the save_to_database method with sample data"""
    print("Testing save_to_database method...")

    # Create sample DataFrame similar to what IBKR returns
    timestamps = pd.date_range(start='2023-01-01', end='2023-01-02', freq='1min')
    sample_data = []
    for ts in timestamps:
        sample_data.append({
            'timestamp': ts,
            'open': 100.0 + len(sample_data) * 0.01,
            'high': 101.0 + len(sample_data) * 0.01,
            'low': 99.0 + len(sample_data) * 0.01,
            'close': 100.5 + len(sample_data) * 0.01,
            'volume': 1000 + len(sample_data)
        })

    df = pd.DataFrame(sample_data)
    print(f"Sample DataFrame: {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"Data types:\n{df.dtypes}")
    print(f"First few rows:\n{df.head()}")

    # Test save_to_database
    collector = IBKRCollector()
    result = collector.save_to_database('TEST_SYMBOL', df, '1min', 'Test Symbol')

    print(f"Save result: {result}")

    # Check if data was saved
    db = SessionLocal()
    try:
        ticker = db.query(Ticker).filter(Ticker.symbol == 'TEST_SYMBOL').first()
        if ticker:
            count = db.query(HistoricalData).filter(HistoricalData.ticker_id == ticker.id).count()
            print(f"Records in database: {count}")
        else:
            print("Ticker not found in database")
    finally:
        db.close()

if __name__ == "__main__":
    test_save_to_database()