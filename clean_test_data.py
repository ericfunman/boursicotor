#!/usr/bin/env python3
"""
Clean test data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import SessionLocal, HistoricalData, Ticker

db = SessionLocal()
try:
    # Delete test tickers and their data
    test_symbols = ['TEST_SYMBOL', 'WLN_TEST', 'WLN_DEBUG', 'WLN_DEBUG2']
    for symbol in test_symbols:
        ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if ticker:
            db.query(HistoricalData).filter(HistoricalData.ticker_id == ticker.id).delete()
            db.delete(ticker)
            print(f"Deleted {symbol}")

    db.commit()
    print("Test data cleaned")
finally:
    db.close()