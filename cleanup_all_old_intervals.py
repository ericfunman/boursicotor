#!/usr/bin/env python
"""Complete cleanup: delete ALL old 1day intervals for ALL tickers"""
from backend.models import SessionLocal, HistoricalData, Ticker
from loguru import logger

db = SessionLocal()
try:
    # Get all tickers
    all_tickers = db.query(Ticker).all()
    total_deleted = 0
    
    for ticker in all_tickers:
        # Count old 1day records
        old_records = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id,
            HistoricalData.interval == '1day'
        ).all()
        
        if old_records:
            print(f"Found {len(old_records)} old 1day records for {ticker.symbol}")
            for rec in old_records[:3]:
                print(f"  - {rec.close}€ @ {rec.timestamp}")
            
            # Delete them
            deleted = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker.id,
                HistoricalData.interval == '1day'
            ).delete()
            db.commit()
            total_deleted += deleted
            print(f"✅ Deleted {deleted} old 1day records for {ticker.symbol}\n")
    
    print(f"\n🎉 TOTAL: Deleted {total_deleted} old 1day records across all tickers")
    
finally:
    db.close()
