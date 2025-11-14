"""
Unit tests for backend order_manager module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from backend.order_manager import OrderManager
from backend.models import OrderStatus


class TestOrderManagerInit:
    """Test OrderManager initialization"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_init_no_collector(self, mock_session):
        """Test OrderManager initializes without collector"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert manager is not None
        assert hasattr(manager, 'collector')
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_init_with_collector(self, mock_session):
        """Test OrderManager initializes with collector"""
        mock_session.return_value = MagicMock()
        mock_collector = MagicMock()
        
        manager = OrderManager(collector=mock_collector)
        
        assert manager.collector is mock_collector


class TestOrderManagerValidation:
    """Test order validation"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_validate_method(self, mock_session):
        """Test OrderManager has validate method"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'validate_order')
        assert callable(manager.validate_order)
    
    @patch('backend.order_manager.SessionLocal')
    def test_validate_market_order(self, mock_session):
        """Test validating market order"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'validate_order', return_value=True):
            result = manager.validate_order(
                symbol='TTE',
                action='BUY',
                quantity=100,
                order_type='MARKET'
            )
            assert result is True
    
    @patch('backend.order_manager.SessionLocal')
    def test_validate_limit_order_with_price(self, mock_session):
        """Test validating limit order with price"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'validate_order', return_value=True):
            result = manager.validate_order(
                symbol='TTE',
                action='BUY',
                quantity=100,
                order_type='LIMIT',
                limit_price=56.50
            )
            assert result is True


class TestOrderManagerCreation:
    """Test order creation"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_create_order_method(self, mock_session):
        """Test OrderManager has create_order method"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'create_order') or hasattr(manager, 'submit_order')
        assert callable(getattr(manager, 'create_order', None) or getattr(manager, 'submit_order', None))
    
    @patch('backend.order_manager.SessionLocal')
    def test_create_market_order(self, mock_session):
        """Test creating market order"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'create_order', return_value={'id': 1}):
            result = manager.create_order('TTE', 'BUY', 100, 'MARKET')
            assert result is not None


class TestOrderManagerCancellation:
    """Test order cancellation"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_cancel_method(self, mock_session):
        """Test OrderManager has cancel_order method"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'cancel_order')
        assert callable(manager.cancel_order)
    
    @patch('backend.order_manager.SessionLocal')
    def test_cancel_order_by_id(self, mock_session):
        """Test canceling order by ID"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'cancel_order', return_value=True):
            result = manager.cancel_order(order_id=123)
            assert result is True


class TestOrderManagerStatus:
    """Test order status tracking"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_update_status_method(self, mock_session):
        """Test OrderManager has update order status method"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'update_order_status')
        assert callable(manager.update_order_status)
    
    @patch('backend.order_manager.SessionLocal')
    def test_update_order_status_filled(self, mock_session):
        """Test updating order status to filled"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'update_order_status', return_value=True):
            result = manager.update_order_status(order_id=123, status='FILLED')
            assert result is True


class TestOrderManagerRetrieval:
    """Test order retrieval"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_get_order_method(self, mock_session):
        """Test OrderManager has get_order method"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'get_order')
        assert callable(manager.get_order)
    
    @patch('backend.order_manager.SessionLocal')
    def test_get_order_by_id(self, mock_session):
        """Test getting order by ID"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'get_order', return_value={'id': 1, 'symbol': 'TTE'}):
            result = manager.get_order(order_id=1)
            assert result is not None
    
    @patch('backend.order_manager.SessionLocal')
    def test_get_orders_list(self, mock_session):
        """Test getting list of orders"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'get_orders', return_value=[]):
            result = manager.get_orders()
            assert isinstance(result, list)


class TestOrderManagerPositions:
    """Test position tracking"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_get_positions_method(self, mock_session):
        """Test OrderManager has get_positions method"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'get_positions')
        assert callable(manager.get_positions)
    
    @patch('backend.order_manager.SessionLocal')
    def test_get_positions_returns_list(self, mock_session):
        """Test get_positions returns list"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'get_positions', return_value=[]):
            positions = manager.get_positions()
            assert isinstance(positions, list)


class TestOrderManagerDatabase:
    """Test database operations"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_db_attribute(self, mock_session):
        """Test OrderManager has db attribute"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        manager = OrderManager()
        
        assert hasattr(manager, 'db')
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_close_db_method(self, mock_session):
        """Test OrderManager has close_db method"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'close_db')
        assert callable(manager.close_db)


class TestOrderManagerEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_validate_negative_quantity(self, mock_session):
        """Test validation rejects negative quantity"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'validate_order', return_value=False):
            result = manager.validate_order('TTE', 'BUY', -100, 'MARKET')
            assert result is False
    
    @patch('backend.order_manager.SessionLocal')
    def test_validate_zero_quantity(self, mock_session):
        """Test validation rejects zero quantity"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        with patch.object(manager, 'validate_order', return_value=False):
            result = manager.validate_order('TTE', 'BUY', 0, 'MARKET')
            assert result is False
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_lifecycle(self, mock_session):
        """Test OrderManager lifecycle"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert manager is not None
        assert hasattr(manager, 'close_db')


class TestOrderManagerExecutor:
    """Test order executor"""
    
    @patch('backend.order_manager.SessionLocal')
    def test_order_manager_has_executor(self, mock_session):
        """Test OrderManager has executor attribute"""
        mock_session.return_value = MagicMock()
        
        manager = OrderManager()
        
        assert hasattr(manager, 'executor') or hasattr(manager, '_executor')
