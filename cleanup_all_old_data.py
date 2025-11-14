#!/usr/bin/env python
"""Clean up ALL old 1day interval data - keep only 1min from live_price_thread"""
from backend.models import SessionLocal, HistoricalData
from loguru import logger

db = SessionLocal()
try:
    # Find ALL 1day records (old data)
    all_1day_records = db.query(HistoricalData).filter(
        HistoricalData.interval == '1day'
    ).all()
    
    print(f'Found {len(all_1day_records)} total 1day records to delete')
    for rec in all_1day_records[:10]:
        print(f'  - Ticker ID {rec.ticker_id}: {rec.close}€ @ {rec.timestamp} ({rec.interval})')
    
    # Delete ALL 1day records
    count = db.query(HistoricalData).filter(
        HistoricalData.interval == '1day'
    ).delete()
    db.commit()
    
    print(f'✅ Deleted {count} old 1day records')
    
    # Show what's left
    remaining = db.query(HistoricalData).filter(
        HistoricalData.interval == '1min'
    ).count()
    print(f'✅ Remaining 1min records: {remaining}')
    
finally:
    db.close()
