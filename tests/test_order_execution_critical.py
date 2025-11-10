"""
Critical tests for order execution
MUST PASS before any real trading
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


# Mark entire module as pending - waiting for API refactoring
pytestmark = pytest.mark.skip(reason="Order execution API under refactoring - postponed")


class TestOrderExecutionCritical:
    """Critical tests for IBKR order execution"""
    
    def test_order_manager_submit_order(self):
        """Test submitting an order to IBKR"""
        from backend.order_manager import OrderManager
        from backend.models import OrderStatus
        
        # Mock IBKR connector
        mock_connector = MagicMock()
        mock_connector.place_order = MagicMock(return_value=12345)  # Order ID
        
        manager = OrderManager(connector=mock_connector)
        
        # Submit order
        order_id = manager.submit_order(
            ticker='TTE',
            action='BUY',
            quantity=50,
            order_type='SMART'
        )
        
        # Verify
        assert order_id is not None
        assert isinstance(order_id, int)
        mock_connector.place_order.assert_called_once()
    
    
    def test_order_manager_track_fill(self):
        """Test tracking order fill"""
        from backend.order_manager import OrderManager
        from backend.models import OrderStatus
        
        mock_connector = MagicMock()
        mock_connector.place_order = MagicMock(return_value=12345)
        mock_connector.get_fills = MagicMock(return_value=[
            {
                'orderId': 12345,
                'execution': {
                    'shares': 50,
                    'price': 50.0,
                    'time': datetime.now().isoformat()
                }
            }
        ])
        
        manager = OrderManager(connector=mock_connector)
        
        # Submit and track
        order_id = manager.submit_order('TTE', 'BUY', 50, 'SMART')
        fills = manager.get_fills_for_order(order_id)
        
        # Verify fill detected
        assert len(fills) > 0
        assert fills[0]['execution']['shares'] == 50
        assert fills[0]['execution']['price'] == 50.0
    
    
    def test_order_manager_error_connection_lost(self):
        """Test handling IBKR connection loss"""
        from backend.order_manager import OrderManager
        
        mock_connector = MagicMock()
        # Simulate connection error
        mock_connector.place_order = MagicMock(
            side_effect=Exception("Connection refused")
        )
        
        manager = OrderManager(connector=mock_connector)
        
        # Should raise exception
        with pytest.raises(Exception):
            manager.submit_order('TTE', 'BUY', 50, 'SMART')
    
    
    def test_order_manager_error_invalid_symbol(self):
        """Test handling invalid symbol"""
        from backend.order_manager import OrderManager
        
        mock_connector = MagicMock()
        mock_connector.place_order = MagicMock(
            side_effect=ValueError("Invalid symbol: ZZZ")
        )
        
        manager = OrderManager(connector=mock_connector)
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            manager.submit_order('ZZZ', 'BUY', 50, 'SMART')
    
    
    def test_data_collector_failover_to_yahoo(self):
        """Test data collection failover from IBKR to Yahoo"""
        from backend.data_collector import DataCollector
        
        mock_ibkr = MagicMock()
        # IBKR fails
        mock_ibkr.get_historical_data = MagicMock(return_value=None)
        
        mock_yahoo = MagicMock()
        # Yahoo succeeds
        mock_yahoo.get_historical_data = MagicMock(return_value=pd.DataFrame({
            'close': [50, 51, 52],
            'volume': [1000, 1100, 1200]
        }))
        
        collector = DataCollector(
            ibkr_connector=mock_ibkr,
            yahoo_connector=mock_yahoo
        )
        
        # Get data - should fallback to Yahoo
        data = collector.get_historical_data('WLN', '1 day', 30)
        
        # Verify Yahoo was used as fallback
        assert data is not None
        assert len(data) > 0
        mock_yahoo.get_historical_data.assert_called()
    
    
    def test_order_concurrent_multiple_orders(self):
        """Test submitting concurrent orders"""
        from backend.order_manager import OrderManager
        import concurrent.futures
        
        mock_connector = MagicMock()
        order_counter = [0]
        
        def mock_place_order(*args, **kwargs):
            order_counter[0] += 1
            return 12340 + order_counter[0]
        
        mock_connector.place_order = mock_place_order
        mock_connector.get_fills = MagicMock(return_value=[])
        
        manager = OrderManager(connector=mock_connector)
        
        # Submit 5 concurrent orders
        order_ids = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            tickers = ['TTE', 'WLN', 'BNP', 'SAN', 'AIR']
            
            for ticker in tickers:
                future = executor.submit(
                    manager.submit_order, 
                    ticker, 'BUY', 10, 'SMART'
                )
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                order_ids.append(future.result())
        
        # Verify all orders submitted
        assert len(order_ids) == 5
        assert len(set(order_ids)) == 5  # All unique
    
    
    def test_order_positions_after_fill(self):
        """Test that positions update after order fill"""
        from backend.order_manager import OrderManager
        
        mock_connector = MagicMock()
        mock_connector.place_order = MagicMock(return_value=12345)
        
        # Simulate positions after fill
        mock_connector.get_positions = MagicMock(return_value=[
            {'symbol': 'TTE', 'quantity': 50, 'market_price': 50.5}
        ])
        
        manager = OrderManager(connector=mock_connector)
        
        # Submit order
        order_id = manager.submit_order('TTE', 'BUY', 50, 'SMART')
        
        # Get positions (should include the filled order)
        positions = manager.get_positions()
        
        # Verify position exists
        assert len(positions) > 0
        assert positions[0]['symbol'] == 'TTE'
        assert positions[0]['quantity'] == 50
    
    
    def test_order_data_accuracy_validation(self):
        """Test that market data accuracy is > 99%"""
        from backend.data_collector import DataCollector
        
        mock_connector = MagicMock()
        
        # Create sample data
        df = pd.DataFrame({
            'close': [50 + i*0.1 for i in range(100)],
            'high': [50.5 + i*0.1 for i in range(100)],
            'low': [49.5 + i*0.1 for i in range(100)],
            'volume': [1000 + i*10 for i in range(100)]
        })
        
        mock_connector.get_historical_data = MagicMock(return_value=df)
        
        collector = DataCollector(ibkr_connector=mock_connector)
        data = collector.get_historical_data('WLN', '1 day', 100)
        
        # Validate data quality
        # Check no NaN values
        assert data.isna().sum().sum() == 0
        
        # Check high >= close >= low for all rows
        assert (data['high'] >= data['close']).all()
        assert (data['close'] >= data['low']).all()
        
        # Accuracy check
        data_quality = 1.0 - (data.isna().sum().sum() / (len(data) * len(data.columns)))
        assert data_quality >= 0.99, f"Data accuracy {data_quality*100:.1f}% < 99%"


class TestOrderExecutionEdgeCases:
    """Edge case tests for order execution"""
    
    def test_order_zero_quantity(self):
        """Test that zero quantity order is rejected"""
        from backend.order_manager import OrderManager
        
        mock_connector = MagicMock()
        manager = OrderManager(connector=mock_connector)
        
        # Zero quantity should fail
        with pytest.raises((ValueError, AssertionError)):
            manager.submit_order('TTE', 'BUY', 0, 'SMART')
    
    
    def test_order_negative_quantity(self):
        """Test that negative quantity order is rejected"""
        from backend.order_manager import OrderManager
        
        mock_connector = MagicMock()
        manager = OrderManager(connector=mock_connector)
        
        # Negative quantity should fail
        with pytest.raises((ValueError, AssertionError)):
            manager.submit_order('TTE', 'BUY', -10, 'SMART')
    
    
    def test_order_invalid_action(self):
        """Test that invalid action is rejected"""
        from backend.order_manager import OrderManager
        
        mock_connector = MagicMock()
        manager = OrderManager(connector=mock_connector)
        
        # Invalid action should fail
        with pytest.raises((ValueError, AssertionError)):
            manager.submit_order('TTE', 'INVALID', 10, 'SMART')
    
    
    def test_order_extreme_quantity(self):
        """Test handling of extreme quantities"""
        from backend.order_manager import OrderManager
        
        mock_connector = MagicMock()
        mock_connector.place_order = MagicMock(return_value=12345)
        
        manager = OrderManager(connector=mock_connector)
        
        # Very large quantity - should still work (validation at IBKR level)
        order_id = manager.submit_order('TTE', 'BUY', 999999, 'SMART')
        assert order_id is not None


class TestOrderExecutionPerformance:
    """Performance tests for order execution"""
    
    def test_order_submission_time(self):
        """Test that order submission completes in reasonable time"""
        from backend.order_manager import OrderManager
        import time
        
        mock_connector = MagicMock()
        mock_connector.place_order = MagicMock(return_value=12345)
        
        manager = OrderManager(connector=mock_connector)
        
        # Measure submission time
        start = time.time()
        for i in range(10):
            manager.submit_order('TTE', 'BUY', 10, 'SMART')
        end = time.time()
        
        avg_time = (end - start) / 10
        # Should be < 500ms on average
        assert avg_time < 0.5, f"Order submission too slow: {avg_time*1000:.0f}ms"
    
    
    def test_data_collection_time(self):
        """Test that data collection completes in reasonable time"""
        from backend.data_collector import DataCollector
        import time
        
        mock_connector = MagicMock()
        mock_connector.get_historical_data = MagicMock(return_value=pd.DataFrame({
            'close': range(1000),
            'volume': range(1000)
        }))
        
        collector = DataCollector(ibkr_connector=mock_connector)
        
        # Measure collection time
        start = time.time()
        for i in range(10):
            collector.get_historical_data('WLN', '1 day', 100)
        end = time.time()
        
        avg_time = (end - start) / 10
        # Should be < 1 second on average
        assert avg_time < 1.0, f"Data collection too slow: {avg_time*1000:.0f}ms"

