#!/usr/bin/env python3
"""Module documentation."""

"""
Test streaming collection with large request
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ibkr_collector import IBKRCollector
from backend.models import SessionLocal, HistoricalData, Ticker

def test_streaming():
    """Test streaming collection with a moderate request"""
    print("Testing streaming collection...")
    
    collector = IBKRCollector()
    
    try:
        print("Connecting to IBKR...")
        if not collector.connect():
            print("Failed to connect to IBKR")
            return
        
        print("\nTest 1: Small request (1 week, 1 min)")
        result1 = collector.collect_and_save_streaming(
            symbol='WLN',
            duration='1 W',
            bar_size='1 min',
            interval='1min',
            name='Worldline Test',
            progress_callback=lambda current, total: print(f"  Progress: {current}/{total} chunks")
        )
        
        print(f"Result 1: {result1}")
        print(f"  New: {result1.get('new_records')}, Updated: {result1.get('updated_records')}, Total: {result1.get('total_records')}")
        
        # Verify in database
        db = SessionLocal()
        try:
            ticker = db.query(Ticker).filter(Ticker.symbol == 'WLN').first()
            if ticker:
                count = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker.id,
                    HistoricalData.interval == '1min'
                ).count()
                print(f"  Verified in database: {count:,} records")
        finally:
            db.close()
        
        print("\n✅ Streaming collection test completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if collector.connected:
            collector.disconnect()

if __name__ == "__main__":
    test_streaming()
