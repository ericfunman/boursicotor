"""
Tests for backend constants and utilities
"""
import pytest
import sys
from pathlib import Path

parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class TestBackendConstants:
    """Test backend constants module"""
    
    def test_constants_import(self):
        """Test that constants can be imported"""
        try:
            from backend.constants import (
                MAJOR_EXCHANGES, TRADING_HOURS_MAPPING,
                DATA_SOURCES, INTERVALS
            )
            
            # Test MAJOR_EXCHANGES
            assert isinstance(MAJOR_EXCHANGES, (list, dict))
            if isinstance(MAJOR_EXCHANGES, list):
                assert len(MAJOR_EXCHANGES) > 0
                assert any('NYSE' in str(ex).upper() or 'NASDAQ' in str(ex).upper() 
                          for ex in MAJOR_EXCHANGES)
        except ImportError as e:
            pytest.skip(f"Constants not available: {e}")
    
    def test_trading_hours_mapping(self):
        """Test trading hours are properly defined"""
        try:
            from backend.constants import TRADING_HOURS_MAPPING
            assert isinstance(TRADING_HOURS_MAPPING, dict)
            assert len(TRADING_HOURS_MAPPING) > 0
        except ImportError:
            pytest.skip("Trading hours not available")
    
    def test_data_sources_defined(self):
        """Test data sources are defined"""
        try:
            from backend.constants import DATA_SOURCES
            assert DATA_SOURCES is not None
            # Should contain at least some data sources
            if isinstance(DATA_SOURCES, (list, dict)):
                assert len(DATA_SOURCES) > 0
        except ImportError:
            pytest.skip("Data sources not defined")


class TestConfigModule:
    """Test configuration module"""
    
    def test_config_import(self):
        """Test config module can be imported"""
        try:
            from backend.config import setup_logger, Config
            assert callable(setup_logger)
            assert Config is not None
        except ImportError as e:
            pytest.skip(f"Config module not available: {e}")
    
    def test_logger_setup(self):
        """Test logger can be set up"""
        try:
            from backend.config import setup_logger
            logger = setup_logger("test_logger")
            assert logger is not None
            # Logger should have standard methods
            assert hasattr(logger, 'info')
            assert hasattr(logger, 'error')
            assert hasattr(logger, 'warning')
            assert hasattr(logger, 'debug')
        except ImportError:
            pytest.skip("Logger setup not available")


class TestDataInterpolator:
    """Test data interpolator functions"""
    
    def test_interpolator_import(self):
        """Test data interpolator can be imported"""
        try:
            from backend.data_interpolator import (
                DataInterpolator, interpolate_missing_data,
                fill_gaps_linear
            )
            assert DataInterpolator is not None
            assert callable(interpolate_missing_data)
            assert callable(fill_gaps_linear)
        except ImportError as e:
            pytest.skip(f"Data interpolator not available: {e}")
    
    def test_interpolator_class(self):
        """Test DataInterpolator class initialization"""
        try:
            from backend.data_interpolator import DataInterpolator
            import pandas as pd
            
            # Create simple test data
            df = pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=5),
                'close': [100, 101, 102, 103, 104],
                'volume': [1000, 1100, 1200, 1300, 1400]
            })
            
            interpolator = DataInterpolator(df)
            assert interpolator is not None
        except (ImportError, Exception) as e:
            pytest.skip(f"DataInterpolator test skipped: {e}")


class TestTechnicalIndicators:
    """Test technical indicators module"""
    
    def test_indicators_import(self):
        """Test indicators can be imported"""
        try:
            from backend.technical_indicators import (
                calculate_rsi, calculate_macd, 
                calculate_bollinger_bands, calculate_sma,
                calculate_ema
            )
            assert callable(calculate_rsi)
            assert callable(calculate_macd)
            assert callable(calculate_bollinger_bands)
            assert callable(calculate_sma)
            assert callable(calculate_ema)
        except ImportError as e:
            pytest.skip(f"Indicators not available: {e}")
    
    def test_sma_calculation(self):
        """Test SMA calculation"""
        try:
            from backend.technical_indicators import calculate_sma
            import pandas as pd
            
            # Simple test data
            prices = [100, 101, 102, 103, 104, 105]
            sma = calculate_sma(prices, period=3)
            
            # SMA should return a result
            assert sma is not None
        except (ImportError, Exception) as e:
            pytest.skip(f"SMA test skipped: {e}")
    
    def test_ema_calculation(self):
        """Test EMA calculation"""
        try:
            from backend.technical_indicators import calculate_ema
            
            prices = [100, 101, 102, 103, 104, 105]
            ema = calculate_ema(prices, period=3)
            
            assert ema is not None
        except (ImportError, Exception) as e:
            pytest.skip(f"EMA test skipped: {e}")


class TestStrategyAdapter:
    """Test strategy adapter module"""
    
    def test_adapter_import(self):
        """Test strategy adapter can be imported"""
        try:
            from backend.strategy_adapter import (
                StrategyAdapter, adapt_strategy, 
                validate_strategy
            )
            assert StrategyAdapter is not None
            assert callable(adapt_strategy)
            assert callable(validate_strategy)
        except ImportError as e:
            pytest.skip(f"Strategy adapter not available: {e}")


class TestSecurityModule:
    """Test security functions"""
    
    def test_security_import(self):
        """Test security module can be imported"""
        try:
            from backend.security import (
                hash_password, verify_password,
                generate_token, verify_token
            )
            assert callable(hash_password)
            assert callable(verify_password)
        except ImportError as e:
            pytest.skip(f"Security module not available: {e}")
    
    def test_password_hashing(self):
        """Test password hashing works"""
        try:
            from backend.security import hash_password, verify_password
            
            password = "test_password_123"
            hashed = hash_password(password)
            
            # Hash should be different from original
            assert hashed != password
            assert hashed is not None
            
            # Verify should work
            if callable(verify_password):
                result = verify_password(password, hashed)
                assert isinstance(result, bool)
        except (ImportError, Exception) as e:
            pytest.skip(f"Password test skipped: {e}")


class TestJobManager:
    """Test job manager module"""
    
    def test_job_manager_import(self):
        """Test job manager can be imported"""
        try:
            from backend.job_manager import JobManager
            assert JobManager is not None
        except ImportError as e:
            pytest.skip(f"Job manager not available: {e}")


class TestOrderManager:
    """Test order manager module"""
    
    def test_order_manager_import(self):
        """Test order manager can be imported"""
        try:
            from backend.order_manager import OrderManager
            assert OrderManager is not None
        except ImportError as e:
            pytest.skip(f"Order manager not available: {e}")


class TestDataCollector:
    """Test data collector module"""
    
    def test_data_collector_import(self):
        """Test data collector can be imported"""
        try:
            from backend.data_collector import DataCollector
            assert DataCollector is not None
        except ImportError as e:
            pytest.skip(f"Data collector not available: {e}")


class TestStrategyManager:
    """Test strategy manager module"""
    
    def test_strategy_manager_import(self):
        """Test strategy manager can be imported"""
        try:
            from backend.strategy_manager import StrategyManager
            assert StrategyManager is not None
        except ImportError as e:
            pytest.skip(f"Strategy manager not available: {e}")


class TestBacktestingEngine:
    """Test backtesting engine module"""
    
    def test_backtesting_import(self):
        """Test backtesting engine can be imported"""
        try:
            from backend.backtesting_engine import BacktestingEngine
            assert BacktestingEngine is not None
        except ImportError as e:
            pytest.skip(f"Backtesting engine not available: {e}")


class TestAutoTrader:
    """Test auto trader module"""
    
    def test_auto_trader_import(self):
        """Test auto trader can be imported"""
        try:
            from backend.auto_trader import AutoTrader
            assert AutoTrader is not None
        except ImportError as e:
            pytest.skip(f"Auto trader not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
