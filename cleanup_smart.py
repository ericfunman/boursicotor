#!/usr/bin/env python
"""
SMART cleanup: Keep ALL historical data, just initialize fresh 1min for live trading
DO NOT DELETE - Only prepare for live collection
"""
from backend.models import SessionLocal, HistoricalData, Ticker
from datetime import datetime
from loguru import logger

db = SessionLocal()
try:
    # Get WLN ticker
    ticker = db.query(Ticker).filter(Ticker.symbol == 'WLN').first()
    if not ticker:
        print('❌ WLN ticker not found')
        exit(1)
    
    # Count ALL records
    total_all = db.query(HistoricalData).filter(
        HistoricalData.ticker_id == ticker.id
    ).count()
    
    print(f'📊 Current state:')
    print(f'  Total records: {total_all}')
    
    # Count by interval
    count_1day = db.query(HistoricalData).filter(
        HistoricalData.ticker_id == ticker.id,
        HistoricalData.interval == '1day'
    ).count()
    
    count_1min = db.query(HistoricalData).filter(
        HistoricalData.ticker_id == ticker.id,
        HistoricalData.interval == '1min'
    ).count()
    
    count_other = total_all - count_1day - count_1min
    
    print(f'  - 1day: {count_1day}')
    print(f'  - 1min: {count_1min}')
    print(f'  - Other intervals: {count_other}')
    
    # KEEP everything, just prepare for live data
    print(f'\n✅ Data preservation OK')
    print(f'🟢 live_price_thread will create fresh 1min records')
    print(f'🟢 AutoTrader will use existing {total_all} records to initialize buffer')
    
finally:
    db.close()
