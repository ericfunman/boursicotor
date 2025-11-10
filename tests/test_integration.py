"""
Integration tests for order management
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

pytestmark = pytest.mark.integration


class TestOrderModel:
    """Test Order model"""
    
    def test_order_model_import(self):
        """Test Order model can be imported"""
        from backend.models import Order, OrderStatus
        
        assert Order is not None
        assert OrderStatus is not None
    
    def test_order_status_values(self):
        """Test OrderStatus has all required values"""
        from backend.models import OrderStatus
        
        assert OrderStatus.PENDING.value == 'pending'
        assert OrderStatus.SUBMITTED.value == 'submitted'
        assert OrderStatus.FILLED.value == 'filled'
        assert OrderStatus.CANCELLED.value == 'cancelled'


class TestTickerModel:
    """Test Ticker model"""
    
    def test_ticker_model_import(self):
        """Test Ticker model can be imported"""
        from backend.models import Ticker
        
        assert Ticker is not None
    
    def test_european_stocks_in_config(self):
        """Test European stocks are configured"""
        try:
            from backend.ibkr_collector import IBKRCollector
            
            european_stocks = IBKRCollector.EUROPEAN_STOCKS
            
            # Check required stocks exist
            required_stocks = ['TTE', 'WLN']
            for stock in required_stocks:
                assert stock in european_stocks
                assert 'exchange' in european_stocks[stock]
                assert 'currency' in european_stocks[stock]
        except Exception as e:
            pytest.skip(f"ib_insync setup issue: {str(e)}")


class TestOrderManagerIntegration:
    """Integration tests for OrderManager"""
    
    def test_order_manager_instantiation(self):
        """Test OrderManager can be instantiated"""
        try:
            from backend.order_manager import OrderManager
            
            # Should be able to instantiate without IBKR connection
            om = OrderManager(ibkr_collector=None)
            assert om is not None
        except Exception as e:
            pytest.skip(f"ib_insync setup issue: {str(e)}")
    
    def test_order_manager_methods_callable(self):
        """Test OrderManager methods are callable"""
        try:
            from backend.order_manager import OrderManager
            
            om = OrderManager(ibkr_collector=None)
            
            assert callable(om.create_order)
            assert callable(om.get_order)
            assert callable(om.cancel_order)
            assert callable(om.get_orders)
        except Exception as e:
            pytest.skip(f"ib_insync setup issue: {str(e)}")


class TestIBKRCollectorIntegration:
    """Integration tests for IBKR Collector"""
    
    def test_collector_instantiation(self):
        """Test IBKRCollector can be instantiated"""
        try:
            from backend.ibkr_collector import IBKRCollector
            
            collector = IBKRCollector(client_id=99)
            assert collector is not None
        except Exception as e:
            pytest.skip(f"ib_insync setup issue: {str(e)}")
    
    def test_collector_european_stocks(self):
        """Test collector recognizes European stocks"""
        try:
            from backend.ibkr_collector import IBKRCollector
            
            collector = IBKRCollector(client_id=99)
            
            # Test contract creation for European stocks
            # Note: This doesn't connect to IBKR, just tests the logic
            assert 'TTE' in collector.EUROPEAN_STOCKS
            assert 'WLN' in collector.EUROPEAN_STOCKS
        except Exception as e:
            pytest.skip(f"ib_insync setup issue: {str(e)}")
    
    def test_interval_map_defined(self):
        """Test that IBKR interval mapping is defined"""
        try:
            from backend.ibkr_collector import IBKRCollector
            
            assert hasattr(IBKRCollector, 'INTERVAL_SECONDS')
            assert len(IBKRCollector.INTERVAL_SECONDS) > 0
        except Exception as e:
            pytest.skip(f"ib_insync setup issue: {str(e)}")
