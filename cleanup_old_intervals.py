#!/usr/bin/env python
"""Clean up old 1day interval data that interferes with 1min live price collection"""
from backend.models import SessionLocal, HistoricalData, Ticker
from loguru import logger

db = SessionLocal()
try:
    # Find WLN ticker
    ticker = db.query(Ticker).filter(Ticker.symbol == 'WLN').first()
    if ticker:
        # Count old 1day records
        old_records = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id,
            HistoricalData.interval == '1day'
        ).all()
        
        print(f'Found {len(old_records)} old 1day records for WLN')
        for rec in old_records[:5]:
            print(f'  - {rec.close}€ @ {rec.timestamp}')
        
        # Delete them
        db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id,
            HistoricalData.interval == '1day'
        ).delete()
        db.commit()
        print(f'✅ Deleted {len(old_records)} old 1day records')
    else:
        print('WLN ticker not found')
finally:
    db.close()
