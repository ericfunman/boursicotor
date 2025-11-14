#!/usr/bin/env python
"""AGGRESSIVE cleanup: Delete ALL 1day records, keep ONLY 1min for live trading"""
from backend.models import SessionLocal, HistoricalData, Ticker
from loguru import logger

db = SessionLocal()
try:
    # Get WLN ticker
    ticker = db.query(Ticker).filter(Ticker.symbol == 'WLN').first()
    if not ticker:
        print('❌ WLN ticker not found')
        exit(1)
    
    # Count ALL records by interval
    all_records = db.query(HistoricalData).filter(
        HistoricalData.ticker_id == ticker.id
    ).all()
    
    records_1day = [r for r in all_records if r.interval == '1day']
    records_1min = [r for r in all_records if r.interval == '1min']
    
    print(f'📊 Current DB state for WLN:')
    print(f'  - 1day records: {len(records_1day)}')
    print(f'  - 1min records: {len(records_1min)}')
    print(f'  - Total: {len(all_records)}')
    
    # Show oldest and newest 1day
    if records_1day:
        print(f'\n1day records (oldest first):')
        records_1day_sorted = sorted(records_1day, key=lambda x: x.timestamp)
        for r in records_1day_sorted[:3]:
            print(f'  - {r.close}€ @ {r.timestamp}')
        print(f'  ... (showing 3 of {len(records_1day)})')
    
    # Show newest 1min
    if records_1min:
        print(f'\n1min records (newest first):')
        records_1min_sorted = sorted(records_1min, key=lambda x: x.timestamp, reverse=True)
        for r in records_1min_sorted[:5]:
            print(f'  - {r.close}€ @ {r.timestamp}')
    
    # DELETE ALL 1day records
    print(f'\n🗑️  Deleting ALL {len(records_1day)} old 1day records...')
    db.query(HistoricalData).filter(
        HistoricalData.ticker_id == ticker.id,
        HistoricalData.interval == '1day'
    ).delete()
    db.commit()
    
    print(f'✅ DELETED {len(records_1day)} old 1day records')
    
    # Verify
    remaining_1day = db.query(HistoricalData).filter(
        HistoricalData.ticker_id == ticker.id,
        HistoricalData.interval == '1day'
    ).count()
    
    remaining_1min = db.query(HistoricalData).filter(
        HistoricalData.ticker_id == ticker.id,
        HistoricalData.interval == '1min'
    ).count()
    
    print(f'\n✅ Final DB state:')
    print(f'  - 1day records: {remaining_1day}')
    print(f'  - 1min records: {remaining_1min}')
    
    if remaining_1min > 0:
        newest_1min = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id,
            HistoricalData.interval == '1min'
        ).order_by(HistoricalData.timestamp.desc()).first()
        print(f'\n🟢 Newest 1min price: {newest_1min.close}€ @ {newest_1min.timestamp}')
    
finally:
    db.close()
