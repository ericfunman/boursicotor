"""
Unit tests for backend modules
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Test backend.config module"""
    
    def test_config_loads(self):
        """Test that configuration loads successfully"""
        from backend.config import logger, FRENCH_TICKERS
        
        assert logger is not None
        assert isinstance(FRENCH_TICKERS, dict)
        assert len(FRENCH_TICKERS) > 0
    
    def test_logger_exists(self):
        """Test that logger is configured"""
        from backend.config import logger
        
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')


class TestModelsImport:
    """Test that models import correctly"""
    
    def test_models_import(self):
        """Test models can be imported"""
        from backend.models import Order, OrderStatus, Ticker, SessionLocal
        
        assert Order is not None
        assert OrderStatus is not None
        assert Ticker is not None
        assert SessionLocal is not None
    
    def test_order_status_enum(self):
        """Test OrderStatus enum values"""
        from backend.models import OrderStatus
        
        assert hasattr(OrderStatus, 'PENDING')
        assert hasattr(OrderStatus, 'SUBMITTED')
        assert hasattr(OrderStatus, 'FILLED')
        assert hasattr(OrderStatus, 'CANCELLED')


class TestIBKRCollectorImport:
    """Test IBKR collector can be imported"""
    
    @pytest.mark.skip(reason="ib_insync requires asyncio event loop setup on Windows")
    def test_collector_import(self):
        """Test IBKRCollector can be imported"""
        from backend.ibkr_collector import IBKRCollector
        
        assert IBKRCollector is not None
    
    @pytest.mark.skip(reason="ib_insync requires asyncio event loop setup on Windows")
    def test_european_stocks_defined(self):
        """Test that European stocks are defined"""
        from backend.ibkr_collector import IBKRCollector
        
        assert hasattr(IBKRCollector, 'EUROPEAN_STOCKS')
        assert 'TTE' in IBKRCollector.EUROPEAN_STOCKS
        assert 'WLN' in IBKRCollector.EUROPEAN_STOCKS


class TestOrderManagerImport:
    """Test OrderManager can be imported"""
    
    @pytest.mark.skip(reason="ib_insync requires asyncio event loop setup on Windows")
    def test_order_manager_import(self):
        """Test OrderManager can be imported"""
        from backend.order_manager import OrderManager
        
        assert OrderManager is not None
    
    @pytest.mark.skip(reason="ib_insync requires asyncio event loop setup on Windows")
    def test_order_manager_methods(self):
        """Test OrderManager has required methods"""
        from backend.order_manager import OrderManager
        
        required_methods = [
            'create_order',
            'get_order',
            'get_orders',
            'cancel_order',
            'check_pending_submissions'
        ]
        
        for method in required_methods:
            assert hasattr(OrderManager, method), f"Missing method: {method}"
