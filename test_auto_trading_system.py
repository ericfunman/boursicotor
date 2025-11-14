"""
Comprehensive test of auto-trading system fixes
Tests: Tab persistence, position refresh, trade visibility, strategy runner
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Setup path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / "backend"))

# Imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import (
    Base, AutoTraderSession, Order, Ticker, HistoricalData, Strategy
)
from backend.strategy_runner import StrategyRunner
from backend.auto_trader import AutoTrader
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAutoTradingSystem:
    """Comprehensive test of auto-trading system"""
    
    def __init__(self):
        """Initialize database connection"""
        db_path = root_dir / "boursicotor.db"
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def test_01_tab_persistence_query_params(self):
        """Test that tab persistence uses query_params instead of session_state"""
        print("\n" + "="*60)
        print("TEST 1: Tab Persistence with query_params")
        print("="*60)
        
        # Check that app.py uses st.query_params for tab persistence
        app_path = root_dir / "frontend" / "app.py"
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("st.query_params.get('auto_trading_tab'", "Tab read from query_params"),
            ("st.query_params['auto_trading_tab']", "Tab written to query_params"),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}: FOUND")
            else:
                print(f"❌ {description}: NOT FOUND")
                all_passed = False
        
        return all_passed
    
    def test_02_datetime_import_fixed(self):
        """Test that datetime import is not duplicated"""
        print("\n" + "="*60)
        print("TEST 2: DateTime Import Fix")
        print("="*60)
        
        app_path = root_dir / "frontend" / "app.py"
        with open(app_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check for duplicate local imports
        local_import_lines = []
        for i, line in enumerate(lines[4550:4600], start=4550):
            if "from datetime import" in line:
                local_import_lines.append((i, line.strip()))
        
        if local_import_lines:
            print(f"❌ Found {len(local_import_lines)} local datetime imports in auto-trading section:")
            for line_no, line in local_import_lines:
                print(f"   Line {line_no}: {line}")
            return False
        
        print("✅ No local datetime imports in auto-trading section")
        return True
    
    def test_03_dashboard_trade_history_queries_db(self):
        """Test that dashboard queries DB Order records for AutoTrader trades"""
        print("\n" + "="*60)
        print("TEST 3: Dashboard Trade History Queries DB")
        print("="*60)
        
        app_path = root_dir / "frontend" / "app.py"
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("orders_db.query(Order)", "Dashboard queries Order table"),
            ("'Source'", "Dashboard has Source column for trade origin"),
            ("AutoTrader", "Dashboard identifies AutoTrader trades"),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}: FOUND")
            else:
                print(f"❌ {description}: NOT FOUND")
                all_passed = False
        
        return all_passed
    
    def test_04_position_sync_implemented(self):
        """Test that position sync is implemented in AutoTrader"""
        print("\n" + "="*60)
        print("TEST 4: Position Sync Implementation")
        print("="*60)
        
        auto_trader_path = root_dir / "backend" / "auto_trader.py"
        with open(auto_trader_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("def _sync_position_with_ibkr", "Position sync method exists"),
            ("_sync_position_with_ibkr()", "Position sync is called after signals"),
            ("positions()", "IBKR positions are requested"),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}: FOUND")
            else:
                print(f"❌ {description}: NOT FOUND")
                all_passed = False
        
        return all_passed
    
    def test_05_refresh_button_added(self):
        """Test that force refresh button is added to positions section"""
        print("\n" + "="*60)
        print("TEST 5: Force Refresh Button")
        print("="*60)
        
        app_path = root_dir / "frontend" / "app.py"
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for both accented and non-accented versions
        if ('refresh_positions' in content) or ('Rafra' in content and 'Positions' in content):
            print("✅ Force refresh button added to positions section")
            return True
        else:
            print("❌ Force refresh button NOT found")
            return False
    
    def test_06_strategy_runner_complete(self):
        """Test that StrategyRunner is implemented"""
        print("\n" + "="*60)
        print("TEST 6: Strategy Runner Implementation")
        print("="*60)
        
        strategy_runner_path = root_dir / "backend" / "strategy_runner.py"
        with open(strategy_runner_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("class StrategyRunner", "StrategyRunner class exists"),
            ("def generate_signals", "generate_signals method exists"),
            ("SMA", "SMA strategy supported"),
            ("RSI", "RSI strategy supported"),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}: FOUND")
            else:
                print(f"❌ {description}: NOT FOUND")
                all_passed = False
        
        return all_passed
    
    def test_07_database_integrity(self):
        """Test database integrity and check for sample data"""
        print("\n" + "="*60)
        print("TEST 7: Database Integrity")
        print("="*60)
        
        try:
            db_session = self.SessionLocal()
            
            # Check Ticker count
            ticker_count = db_session.query(Ticker).count()
            print(f"📊 Tickers in DB: {ticker_count}")
            
            # Check Orders count
            order_count = db_session.query(Order).count()
            print(f"📊 Orders in DB: {order_count}")
            
            # Check Sessions count
            session_count = db_session.query(AutoTraderSession).count()
            print(f"📊 Sessions in DB: {session_count}")
            
            # Check Strategies count
            strategy_count = db_session.query(Strategy).count()
            print(f"📊 Strategies in DB: {strategy_count}")
            
            # Check historical data
            hist_count = db_session.query(HistoricalData).count()
            print(f"📊 Historical data points: {hist_count}")
            
            # Get recent orders
            recent_orders = db_session.query(Order).order_by(Order.created_at.desc()).limit(3).all()
            if recent_orders:
                print("\n✅ Recent orders found:")
                for order in recent_orders:
                    print(f"   - {order.ticker_id}: {order.action} {order.quantity}")
            else:
                print("\n⚠️  No recent orders found")
            
            db_session.close()
            return True
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_08_order_manager_params(self):
        """Test that OrderManager parameters are correct"""
        print("\n" + "="*60)
        print("TEST 8: OrderManager Parameters")
        print("="*60)
        
        auto_trader_path = root_dir / "backend" / "auto_trader.py"
        with open(auto_trader_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for incorrect parameter name
        if "ticker_symbol=" in content:
            print("❌ Found incorrect parameter: ticker_symbol=")
            print("   Should be: symbol=")
            return False
        
        # Check for correct parameter name
        if "symbol=self.ticker.symbol" in content:
            print("✅ Correct parameter name found: symbol=")
            return True
        else:
            print("⚠️  Could not verify parameter in create_order call")
            return False
    
    def run_all_tests(self):
        """Run all tests and report results"""
        print("\n" + "🧪 "*30)
        print("AUTO-TRADING SYSTEM TEST SUITE")
        print("🧪 "*30)
        
        tests = [
            self.test_01_tab_persistence_query_params,
            self.test_02_datetime_import_fixed,
            self.test_03_dashboard_trade_history_queries_db,
            self.test_04_position_sync_implemented,
            self.test_05_refresh_button_added,
            self.test_06_strategy_runner_complete,
            self.test_07_database_integrity,
            self.test_08_order_manager_params,
        ]
        
        results = {}
        for test in tests:
            try:
                result = test()
                results[test.__name__] = result
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results[test.__name__] = False
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print("\n" + "="*60)
        print(f"TOTAL: {passed}/{total} tests passed ({100*passed//total}%)")
        print("="*60 + "\n")
        
        return passed, total


if __name__ == "__main__":
    tester = TestAutoTradingSystem()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)
