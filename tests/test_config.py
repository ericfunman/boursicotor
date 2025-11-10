"""
Configuration and utilities tests
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigModule:
    """Test configuration module"""
    
    def test_config_import(self):
        """Test config can be imported"""
        from backend.config import (
            DATABASE_URL, IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID,
            FRENCH_TICKERS, logger
        )
        
        assert DATABASE_URL is not None
        assert IBKR_HOST is not None
        assert IBKR_PORT is not None
        assert isinstance(IBKR_CLIENT_ID, int)
        assert isinstance(FRENCH_TICKERS, dict)
        assert logger is not None
    
    def test_french_tickers_structure(self):
        """Test FRENCH_TICKERS has correct structure"""
        from backend.config import FRENCH_TICKERS
        
        # Check that tickers are defined
        assert len(FRENCH_TICKERS) > 0
        
        # Sample tickers should exist
        sample_tickers = ['TTE', 'TOTAL', 'WLN', 'BNP', 'OR']
        for ticker in sample_tickers:
            if ticker in FRENCH_TICKERS:
                ticker_data = FRENCH_TICKERS[ticker]
                assert 'name' in ticker_data
                assert 'isin' in ticker_data


class TestLogger:
    """Test logger functionality"""
    
    def test_logger_can_log(self):
        """Test that logger works"""
        from backend.config import logger
        
        # This should not raise an exception
        logger.info("Test message")
        logger.debug("Test debug")
        logger.warning("Test warning")
        
        assert True


class TestDatabaseModels:
    """Test database models"""
    
    def test_models_initialization(self):
        """Test models can be used"""
        from backend.models import Order, Ticker, OrderStatus
        from sqlalchemy import inspect
        
        # Test Order model has required columns
        order_mapper = inspect(Order)
        order_columns = [c.key for c in order_mapper.columns]
        
        required_columns = ['id', 'symbol', 'quantity', 'status']
        for col in required_columns:
            assert col in order_columns
    
    def test_ticker_model_columns(self):
        """Test Ticker model has required columns"""
        from backend.models import Ticker
        from sqlalchemy import inspect
        
        ticker_mapper = inspect(Ticker)
        ticker_columns = [c.key for c in ticker_mapper.columns]
        
        required_columns = ['symbol', 'name']
        for col in required_columns:
            assert col in ticker_columns


class TestDataCollector:
    """Test data collector functionality"""
    
    def test_data_collector_import(self):
        """Test DataCollector can be imported"""
        from backend.data_collector import DataCollector
        
        assert DataCollector is not None
    
    def test_data_collector_methods_exist(self):
        """Test DataCollector has required methods"""
        from backend.data_collector import DataCollector
        
        required_methods = [
            'get_data_with_indicators',
            'get_technical_indicators',
            'prepare_data',
            'calculate_sma',
        ]
        
        for method in required_methods:
            assert hasattr(DataCollector, method)
            assert callable(getattr(DataCollector, method))


class TestUtilsModule:
    """Test utility modules"""
    
    def test_technical_indicators_import(self):
        """Test technical indicators can be imported"""
        from backend.technical_indicators import calculate_rsi, calculate_macd
        
        assert callable(calculate_rsi)
        assert callable(calculate_macd)
