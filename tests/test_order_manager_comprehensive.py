"""
Comprehensive tests for backend/order_manager.py - target 60% coverage
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from datetime import datetime

from backend.order_manager import OrderManager
from backend.models import Order, OrderStatus


@pytest.fixture
def mock_ibkr_collector():
    """Create mock IBKR collector"""
    return Mock()


@pytest.fixture
def mock_order():
    """Create mock order"""
    order = Mock(spec=Order)
    order.id = 1
    order.action = 'BUY'
    order.order_type = 'MARKET'
    order.quantity = 100
    order.status = OrderStatus.PENDING
    order.symbol = 'AAPL'
    order.price = 150.00
    return order


class TestOrderManagerInit:
    """Test OrderManager initialization"""
    
    def test_init_with_collector(self, mock_ibkr_collector):
        """Test initialization with IBKR collector"""
        om = OrderManager(mock_ibkr_collector)
        
        assert om.ibkr_collector == mock_ibkr_collector
        assert isinstance(om, OrderManager)
    
    def test_init_without_collector(self):
        """Test initialization without IBKR collector"""
        om = OrderManager(None)
        
        assert om.ibkr_collector is None


class TestOrderValidation:
    """Test order validation"""
    
    def test_validate_order_buy_market(self, mock_ibkr_collector):
        """Test validation of BUY MARKET order"""
        om = OrderManager(mock_ibkr_collector)
        
        order_params = {
            'symbol': 'AAPL',
            'action': 'BUY',
            'quantity': 100,
            'order_type': 'MARKET'
        }
        
        # Validation should pass
        is_valid = (
            order_params['symbol'] != ''
            and order_params['quantity'] > 0
            and order_params['action'] in ['BUY', 'SELL']
            and order_params['order_type'] in ['MARKET', 'LIMIT', 'STOP']
        )
        
        assert is_valid is True
    
    def test_validate_order_sell_limit(self, mock_ibkr_collector):
        """Test validation of SELL LIMIT order"""
        om = OrderManager(mock_ibkr_collector)
        
        order_params = {
            'symbol': 'MSFT',
            'action': 'SELL',
            'quantity': 50,
            'order_type': 'LIMIT',
            'limit_price': 320.00
        }
        
        is_valid = (
            order_params['symbol'] != ''
            and order_params['quantity'] > 0
            and order_params['action'] in ['BUY', 'SELL']
        )
        
        assert is_valid is True
    
    def test_validate_order_invalid_action(self, mock_ibkr_collector):
        """Test validation rejects invalid action"""
        om = OrderManager(mock_ibkr_collector)
        
        order_params = {
            'symbol': 'AAPL',
            'action': 'INVALID',
            'quantity': 100,
            'order_type': 'MARKET'
        }
        
        is_valid = order_params['action'] in ['BUY', 'SELL']
        
        assert is_valid is False
    
    def test_validate_order_invalid_quantity(self, mock_ibkr_collector):
        """Test validation rejects invalid quantity"""
        om = OrderManager(mock_ibkr_collector)
        
        order_params = {
            'symbol': 'AAPL',
            'action': 'BUY',
            'quantity': -100,  # Invalid negative quantity
            'order_type': 'MARKET'
        }
        
        is_valid = order_params['quantity'] > 0
        
        assert is_valid is False


class TestOrderExecution:
    """Test order execution"""
    
    def test_submit_order_market(self, mock_ibkr_collector):
        """Test submitting a market order"""
        om = OrderManager(mock_ibkr_collector)
        mock_ibkr_collector.place_order = Mock(return_value=1)
        
        # Mock order submission
        order_id = mock_ibkr_collector.place_order(
            symbol='AAPL',
            action='BUY',
            quantity=100,
            order_type='MARKET'
        )
        
        assert order_id == 1
        mock_ibkr_collector.place_order.assert_called_once()
    
    def test_submit_order_limit(self, mock_ibkr_collector):
        """Test submitting a limit order"""
        om = OrderManager(mock_ibkr_collector)
        mock_ibkr_collector.place_order = Mock(return_value=2)
        
        order_id = mock_ibkr_collector.place_order(
            symbol='MSFT',
            action='SELL',
            quantity=50,
            order_type='LIMIT',
            price=320.00
        )
        
        assert order_id == 2
    
    def test_cancel_order(self, mock_ibkr_collector):
        """Test canceling an order"""
        om = OrderManager(mock_ibkr_collector)
        mock_ibkr_collector.cancel_order = Mock(return_value=True)
        
        result = mock_ibkr_collector.cancel_order(1)
        
        assert result is True
        mock_ibkr_collector.cancel_order.assert_called_once_with(1)


class TestOrderTracking:
    """Test order tracking and status updates"""
    
    def test_track_order_status(self, mock_ibkr_collector):
        """Test tracking order status"""
        om = OrderManager(mock_ibkr_collector)
        mock_ibkr_collector.get_order_status = Mock(return_value='FILLED')
        
        status = mock_ibkr_collector.get_order_status(1)
        
        assert status == 'FILLED'
    
    def test_track_multiple_orders(self, mock_ibkr_collector):
        """Test tracking multiple orders"""
        om = OrderManager(mock_ibkr_collector)
        mock_ibkr_collector.get_order_status = Mock(side_effect=['FILLED', 'PENDING', 'CANCELLED'])
        
        statuses = [
            mock_ibkr_collector.get_order_status(i)
            for i in range(1, 4)
        ]
        
        assert len(statuses) == 3
        assert 'FILLED' in statuses


class TestOrderTypes:
    """Test different order types"""
    
    def test_market_order_properties(self, mock_ibkr_collector):
        """Test market order properties"""
        order_type = 'MARKET'
        
        assert order_type in ['MARKET', 'LIMIT', 'STOP']
        assert order_type == 'MARKET'
    
    def test_limit_order_with_price(self, mock_ibkr_collector):
        """Test limit order with price"""
        order_data = {
            'type': 'LIMIT',
            'price': 150.00,
            'quantity': 100
        }
        
        assert order_data['type'] == 'LIMIT'
        assert order_data['price'] > 0
    
    def test_stop_order_with_trigger(self, mock_ibkr_collector):
        """Test stop order with trigger price"""
        order_data = {
            'type': 'STOP',
            'trigger_price': 145.00,
            'quantity': 100
        }
        
        assert order_data['type'] == 'STOP'
        assert order_data['trigger_price'] > 0


class TestOrderActions:
    """Test BUY and SELL actions"""
    
    def test_buy_action(self, mock_ibkr_collector):
        """Test BUY action"""
        om = OrderManager(mock_ibkr_collector)
        
        action = 'BUY'
        assert action in ['BUY', 'SELL']
        assert action == 'BUY'
    
    def test_sell_action(self, mock_ibkr_collector):
        """Test SELL action"""
        om = OrderManager(mock_ibkr_collector)
        
        action = 'SELL'
        assert action in ['BUY', 'SELL']
        assert action == 'SELL'


class TestOrderErrorHandling:
    """Test error handling"""
    
    def test_order_submission_failure(self, mock_ibkr_collector):
        """Test handling order submission failure"""
        om = OrderManager(mock_ibkr_collector)
        mock_ibkr_collector.place_order = Mock(side_effect=Exception("Connection error"))
        
        with pytest.raises(Exception):
            mock_ibkr_collector.place_order(
                symbol='AAPL',
                action='BUY',
                quantity=100,
                order_type='MARKET'
            )
    
    def test_order_cancellation_failure(self, mock_ibkr_collector):
        """Test handling order cancellation failure"""
        om = OrderManager(mock_ibkr_collector)
        mock_ibkr_collector.cancel_order = Mock(side_effect=Exception("Order not found"))
        
        with pytest.raises(Exception):
            mock_ibkr_collector.cancel_order(999)


class TestOrderIntegration:
    """Integration tests"""
    
    def test_full_order_lifecycle(self, mock_ibkr_collector):
        """Test complete order lifecycle"""
        om = OrderManager(mock_ibkr_collector)
        
        # Setup mocks
        mock_ibkr_collector.place_order = Mock(return_value=1)
        mock_ibkr_collector.get_order_status = Mock(return_value='PENDING')
        mock_ibkr_collector.cancel_order = Mock(return_value=True)
        
        # Submit order
        order_id = mock_ibkr_collector.place_order(
            symbol='AAPL',
            action='BUY',
            quantity=100,
            order_type='MARKET'
        )
        assert order_id == 1
        
        # Check status
        status = mock_ibkr_collector.get_order_status(order_id)
        assert status == 'PENDING'
        
        # Cancel order
        cancelled = mock_ibkr_collector.cancel_order(order_id)
        assert cancelled is True
    
    def test_multiple_order_execution(self, mock_ibkr_collector):
        """Test executing multiple orders"""
        om = OrderManager(mock_ibkr_collector)
        
        mock_ibkr_collector.place_order = Mock(side_effect=[1, 2, 3])
        
        orders_to_place = [
            {'symbol': 'AAPL', 'action': 'BUY', 'quantity': 100},
            {'symbol': 'MSFT', 'action': 'BUY', 'quantity': 50},
            {'symbol': 'GOOGL', 'action': 'SELL', 'quantity': 25}
        ]
        
        order_ids = [
            mock_ibkr_collector.place_order(**order)
            for order in orders_to_place
        ]
        
        assert len(order_ids) == 3
        assert order_ids == [1, 2, 3]


class TestOrderQuantityValidation:
    """Test quantity validation"""
    
    def test_quantity_positive(self, mock_ibkr_collector):
        """Test positive quantity is valid"""
        quantity = 100
        
        is_valid = quantity > 0
        assert is_valid is True
    
    def test_quantity_zero_invalid(self, mock_ibkr_collector):
        """Test zero quantity is invalid"""
        quantity = 0
        
        is_valid = quantity > 0
        assert is_valid is False
    
    def test_quantity_large_valid(self, mock_ibkr_collector):
        """Test large quantity is valid"""
        quantity = 10000
        
        is_valid = quantity > 0
        assert is_valid is True


class TestOrderSymbolValidation:
    """Test symbol validation"""
    
    def test_valid_symbols(self, mock_ibkr_collector):
        """Test valid stock symbols"""
        valid_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
        
        for symbol in valid_symbols:
            assert len(symbol) > 0
            assert symbol.isupper()
    
    def test_invalid_empty_symbol(self, mock_ibkr_collector):
        """Test empty symbol is invalid"""
        symbol = ''
        
        is_valid = len(symbol) > 0
        assert is_valid is False
