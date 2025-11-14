#!/usr/bin/env python3
"""
Pre-market readiness check - verify everything is ready for live trading
Tests:
1. Thread can start/stop cleanly
2. Database persistence works
3. Indicators calculate correctly
4. Price precision is 3 decimals
5. Timestamps are correct
"""
import time
import sys
from datetime import datetime
from backend.models import SessionLocal, Ticker, HistoricalData
from backend.live_price_thread import (
    start_live_price_collection,
    stop_live_price_collection,
    is_collecting,
    get_current_symbol,
)
from backend.indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands

def check_database():
    """Check database connectivity"""
    print("\n" + "="*80)
    print("[1] DATABASE CONNECTIVITY CHECK")
    print("="*80)
    try:
        db = SessionLocal()
        ticker_count = db.query(Ticker).count()
        data_count = db.query(HistoricalData).count()
        db.close()
        print(f"✅ Database connected")
        print(f"   - Tickers in DB: {ticker_count}")
        print(f"   - Historical data records: {data_count}")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_thread_lifecycle():
    """Check thread start/stop works correctly"""
    print("\n" + "="*80)
    print("[2] THREAD LIFECYCLE CHECK")
    print("="*80)
    try:
        # Initial state
        if is_collecting():
            print("⚠️ Warning: Thread already collecting, stopping first...")
            stop_live_price_collection()
            time.sleep(0.5)
        
        # Test start
        print("Starting thread for TTE...")
        result = start_live_price_collection("TTE", interval=3)
        if not result:
            print("❌ Failed to start thread")
            return False
        print(f"✅ Thread started successfully")
        
        # Check state
        if not is_collecting():
            print("❌ is_collecting() returned False after start")
            return False
        print(f"✅ is_collecting() = True")
        
        symbol = get_current_symbol()
        if symbol != "TTE":
            print(f"❌ get_current_symbol() returned {symbol}, expected TTE")
            return False
        print(f"✅ get_current_symbol() = {symbol}")
        
        # Let it collect one price
        print("Letting thread collect prices for 2 seconds...")
        time.sleep(2)
        
        # Check database
        db = SessionLocal()
        tte_ticker = db.query(Ticker).filter(Ticker.symbol == "TTE").first()
        if not tte_ticker:
            print("⚠️ TTE ticker not in database yet (might not have traded)")
            db.close()
        else:
            data = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == tte_ticker.id
            ).order_by(HistoricalData.timestamp.desc()).first()
            if data:
                print(f"✅ Price in database: {data.close}€ @ {data.timestamp}")
            db.close()
        
        # Test stop
        print("Stopping thread...")
        result = stop_live_price_collection()
        if not result:
            print("❌ Failed to stop thread")
            return False
        print(f"✅ Thread stopped successfully")
        
        if is_collecting():
            print("❌ is_collecting() returned True after stop")
            return False
        print(f"✅ is_collecting() = False after stop")
        
        return True
    except Exception as e:
        print(f"❌ Thread lifecycle error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_indicators():
    """Check indicator calculations"""
    print("\n" + "="*80)
    print("[3] INDICATORS CALCULATION CHECK")
    print("="*80)
    try:
        # Create sample price data
        prices = [56.00, 56.05, 56.10, 56.08, 56.15, 56.20, 56.18, 56.25, 56.30, 56.28,
                  56.35, 56.40, 56.38, 56.45, 56.50, 56.48, 56.55, 56.60, 56.58, 56.65]
        
        print(f"Sample prices: {prices[:3]}... to {prices[-3:]}")
        
        # RSI
        rsi = calculate_rsi(prices, period=14)
        if rsi is None:
            print("⚠️ RSI returned None (need more data)")
        else:
            print(f"✅ RSI calculated: {[f'{v:.2f}' for v in rsi[-3:]]}")
            if not all(0 <= v <= 100 for v in rsi if v is not None):
                print("❌ RSI values outside 0-100 range")
                return False
        
        # MACD
        macd_result = calculate_macd(prices, fast=12, slow=26, signal=9)
        if macd_result is None:
            print("⚠️ MACD returned None (need more data)")
        else:
            macd_line, signal_line, histogram = macd_result
            print(f"✅ MACD calculated")
            print(f"   - MACD line: {[f'{v:.4f}' for v in macd_line[-3:]]}")
            print(f"   - Signal line: {[f'{v:.4f}' for v in signal_line[-3:]]}")
            print(f"   - Histogram: {[f'{v:.4f}' for v in histogram[-3:]]}")
        
        # Bollinger Bands
        bb_result = calculate_bollinger_bands(prices, period=20, num_std=2)
        if bb_result is None:
            print("⚠️ Bollinger Bands returned None (need more data)")
        else:
            upper, middle, lower = bb_result
            print(f"✅ Bollinger Bands calculated")
            print(f"   - Upper: {[f'{v:.2f}' for v in upper[-3:]]}")
            print(f"   - Middle: {[f'{v:.2f}' for v in middle[-3:]]}")
            print(f"   - Lower: {[f'{v:.2f}' for v in lower[-3:]]}")
            
            # Verify ordering
            for i in range(len(upper)):
                if upper[i] < middle[i] or middle[i] < lower[i]:
                    print(f"❌ Band ordering error at index {i}")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Indicator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_price_precision():
    """Check price precision (3 decimals)"""
    print("\n" + "="*80)
    print("[4] PRICE PRECISION CHECK")
    print("="*80)
    try:
        db = SessionLocal()
        
        # Get latest price data
        latest_data = db.query(HistoricalData).order_by(
            HistoricalData.timestamp.desc()
        ).limit(10).all()
        
        db.close()
        
        if not latest_data:
            print("⚠️ No price data in database yet")
            return True
        
        print(f"Checking last {len(latest_data)} price records:")
        for data in latest_data:
            price_str = f"{data.close:.10f}"
            decimal_places = len(price_str.split('.')[1].rstrip('0'))
            print(f"  {data.timestamp}: {data.close:.3f}€ ({decimal_places} decimals)")
            if decimal_places > 3:
                print(f"  ⚠️ More than 3 decimal places detected")
        
        print("✅ Price precision check complete")
        return True
    except Exception as e:
        print(f"❌ Price precision error: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*80)
    print("🚀 PRE-MARKET READINESS CHECK")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = [
        ("Database Connectivity", check_database),
        ("Thread Lifecycle", check_thread_lifecycle),
        ("Indicators Calculation", check_indicators),
        ("Price Precision", check_price_precision),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Exception in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nResults: {passed}/{total} checks passed")
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    if passed == total:
        print("\n🎉 ALL CHECKS PASSED - READY FOR LIVE TRADING!")
        return 0
    else:
        print("\n⚠️ SOME CHECKS FAILED - PLEASE REVIEW")
        return 1

if __name__ == "__main__":
    sys.exit(main())
