"""
Unit tests for backend configuration
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from backend.config import (
    logger,
    DATABASE_URL,
    IBKR_CONFIG,
    TRADING_CONFIG,
    DATA_CONFIG,
)


class TestConfigVariables:
    """Test configuration variables are loaded correctly"""
    
    def test_database_url_loaded(self):
        """Test DATABASE_URL is configured"""
        assert DATABASE_URL is not None
        assert isinstance(DATABASE_URL, str)
        assert 'sqlite:///' in DATABASE_URL
    
    def test_ibkr_config_loaded(self):
        """Test IBKR_CONFIG is configured"""
        assert IBKR_CONFIG is not None
        assert isinstance(IBKR_CONFIG, dict)
        assert 'host' in IBKR_CONFIG
        assert 'port' in IBKR_CONFIG
    
    def test_ibkr_config_host_valid(self):
        """Test IBKR_CONFIG host is valid"""
        assert isinstance(IBKR_CONFIG['host'], str)
        assert len(IBKR_CONFIG['host']) > 0
    
    def test_ibkr_config_port_valid(self):
        """Test IBKR_CONFIG port is valid"""
        assert isinstance(IBKR_CONFIG['port'], int)
        assert IBKR_CONFIG['port'] > 0


class TestLogger:
    """Test logger configuration"""
    
    def test_logger_exists(self):
        """Test logger is configured"""
        assert logger is not None
    
    def test_logger_has_info_method(self):
        """Test logger has info method"""
        assert hasattr(logger, 'info')
        assert callable(logger.info)
    
    def test_logger_has_error_method(self):
        """Test logger has error method"""
        assert hasattr(logger, 'error')
        assert callable(logger.error)
    
    def test_logger_has_warning_method(self):
        """Test logger has warning method"""
        assert hasattr(logger, 'warning')
        assert callable(logger.warning)
    
    def test_logger_has_debug_method(self):
        """Test logger has debug method"""
        assert hasattr(logger, 'debug')
        assert callable(logger.debug)


class TestTradingConfig:
    """Test trading configuration"""
    
    def test_trading_config_loaded(self):
        """Test TRADING_CONFIG is configured"""
        assert TRADING_CONFIG is not None
        assert isinstance(TRADING_CONFIG, dict)
    
    def test_trading_config_has_paper_trading(self):
        """Test TRADING_CONFIG has paper_trading setting"""
        assert 'paper_trading' in TRADING_CONFIG
        assert isinstance(TRADING_CONFIG['paper_trading'], bool)
    
    def test_trading_config_has_max_position(self):
        """Test TRADING_CONFIG has max_position_size"""
        assert 'max_position_size' in TRADING_CONFIG
        assert TRADING_CONFIG['max_position_size'] > 0


class TestDataConfig:
    """Test data collection configuration"""
    
    def test_data_config_loaded(self):
        """Test DATA_CONFIG is configured"""
        assert DATA_CONFIG is not None
        assert isinstance(DATA_CONFIG, dict)
    
    def test_data_config_has_interval(self):
        """Test DATA_CONFIG has default_interval"""
        assert 'default_interval' in DATA_CONFIG
        assert isinstance(DATA_CONFIG['default_interval'], str)
