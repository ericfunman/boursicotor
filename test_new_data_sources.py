#!/usr/bin/env python3
"""
Test script for new data sources: Yahoo Finance, Alpha Vantage, and Polygon.io
"""
import os
from backend.data_collector import DataCollector

def test_data_sources():
    """Test all available data sources"""

    print("🔍 Testing data collection sources...")
    print("=" * 50)

    # Initialize collector
    collector = DataCollector()

    # Test symbol
    symbol = "TTE"  # TotalEnergies
    name = "TotalEnergies"

    # Test each source
    sources = [
        ("Yahoo Finance", lambda: collector._get_yahoo_data(symbol, "1M", "1day")),
        ("Alpha Vantage", lambda: collector._get_alpha_vantage_data(symbol, "1M", "1day") if collector.alpha_vantage_client else None),
        ("Polygon.io", lambda: collector._get_polygon_data(symbol, "1M", "1day") if collector.polygon_client else None),
    ]

    for source_name, get_data_func in sources:
        print(f"\n📊 Testing {source_name}:")
        try:
            df = get_data_func()
            if df is not None and not df.empty:
                print(f"  ✅ Success! Retrieved {len(df)} records")
                print(f"  📅 Date range: {df.index.min()} to {df.index.max()}")
                print(f"  💰 Latest close: {df['close'].iloc[-1]:.2f}€")
            else:
                print("  ❌ No data retrieved")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🎯 To use these sources, add API keys to your .env file:")
    print("   ALPHA_VANTAGE_API_KEY=your_key_here")
    print("   POLYGON_API_KEY=your_key_here")
    print("\n📖 Get free API keys at:")
    print("   • Alpha Vantage: https://www.alphavantage.co/support/#api-key")
    print("   • Polygon.io: https://polygon.io/")

if __name__ == "__main__":
    test_data_sources()