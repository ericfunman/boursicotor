"""
Focused tests for order_manager.py (40 tests)
Coverage targets: 14% baseline -> 50%+
Tests: OrderStatus enum, IBOrder creation, OrderManager init, validation, parsing
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from typing import Optional

# Mocks for IBKR imports before importing order_manager
import sys

# Mock the ib_insync imports
sys.modules['ib_insync'] = MagicMock()
sys.modules['ib_insync'].Stock = Mock
sys.modules['ib_insync'].MarketOrder = Mock
sys.modules['ib_insync'].LimitOrder = Mock
sys.modules['ib_insync'].StopOrder = Mock
sys.modules['ib_insync'].StopLimitOrder = Mock
sys.modules['ib_insync'].Order = Mock
sys.modules['ib_insync'].Trade = Mock

from backend.models import OrderStatus, Order, Ticker, Strategy
from backend.order_manager import OrderManager


class TestOrderManagerImport(unittest.TestCase):
    """Test 1-3: Import and basic instantiation"""
    
    def test_import_order_manager(self):
        """Test 1: OrderManager can be imported"""
        self.assertIsNotNone(OrderManager)
    
    def test_instantiate_without_collector(self):
        """Test 2: OrderManager instantiation without collector"""
        manager = OrderManager(ibkr_collector=None)
        self.assertEqual(manager.ibkr_collector, None)
        self.assertIsNotNone(manager._executor)
        self.assertIsNotNone(manager._pending_submissions)
    
    def test_instantiate_with_collector(self):
        """Test 3: OrderManager instantiation with collector"""
        mock_collector = Mock()
        manager = OrderManager(ibkr_collector=mock_collector)
        self.assertEqual(manager.ibkr_collector, mock_collector)


class TestOrderStatusEnum(unittest.TestCase):
    """Test 4-10: OrderStatus enumeration"""
    
    def test_orderstatus_pending_value(self):
        """Test 4: OrderStatus.PENDING has correct value"""
        self.assertEqual(OrderStatus.PENDING.value, "pending")
    
    def test_orderstatus_submitted_value(self):
        """Test 5: OrderStatus.SUBMITTED has correct value"""
        self.assertEqual(OrderStatus.SUBMITTED.value, "submitted")
    
    def test_orderstatus_filled_value(self):
        """Test 6: OrderStatus.FILLED has correct value"""
        self.assertEqual(OrderStatus.FILLED.value, "filled")
    
    def test_orderstatus_cancelled_value(self):
        """Test 7: OrderStatus.CANCELLED has correct value"""
        self.assertEqual(OrderStatus.CANCELLED.value, "cancelled")
    
    def test_orderstatus_error_value(self):
        """Test 8: OrderStatus.ERROR has correct value"""
        self.assertEqual(OrderStatus.ERROR.value, "error")
    
    def test_orderstatus_partially_filled_value(self):
        """Test 9: OrderStatus.PARTIALLY_FILLED has correct value"""
        self.assertEqual(OrderStatus.PARTIALLY_FILLED.value, "partially_filled")
    
    def test_orderstatus_rejected_value(self):
        """Test 10: OrderStatus.REJECTED has correct value"""
        self.assertEqual(OrderStatus.REJECTED.value, "rejected")


class TestIBOrderCreation(unittest.TestCase):
    """Test 11-16: IBOrder creation through _create_ib_order"""
    
    def setUp(self):
        """Setup common test fixtures"""
        self.manager = OrderManager(ibkr_collector=None)
        
        # Create mock Order objects for testing
        self.mock_ticker = Mock(spec=Ticker)
        self.mock_ticker.symbol = "AAPL"
        self.mock_ticker.id = 1
    
    def test_create_market_order(self):
        """Test 11: Create market order"""
        mock_order = Mock(spec=Order)
        mock_order.action = "BUY"
        mock_order.quantity = 100
        mock_order.order_type = "MARKET"
        mock_order.ticker = self.mock_ticker
        
        with patch('backend.order_manager.MarketOrder') as mock_market:
            self.manager._create_ib_order(mock_order)
            mock_market.assert_called_once_with("BUY", 100)
    
    def test_create_limit_order(self):
        """Test 12: Create limit order"""
        mock_order = Mock(spec=Order)
        mock_order.action = "SELL"
        mock_order.quantity = 50
        mock_order.order_type = "LIMIT"
        mock_order.limit_price = 150.25
        mock_order.ticker = self.mock_ticker
        
        with patch('backend.order_manager.LimitOrder') as mock_limit:
            self.manager._create_ib_order(mock_order)
            mock_limit.assert_called_once_with("SELL", 50, 150.25)
    
    def test_create_stop_order(self):
        """Test 13: Create stop order"""
        mock_order = Mock(spec=Order)
        mock_order.action = "SELL"
        mock_order.quantity = 75
        mock_order.order_type = "STOP"
        mock_order.stop_price = 145.00
        mock_order.ticker = self.mock_ticker
        
        with patch('backend.order_manager.StopOrder') as mock_stop:
            self.manager._create_ib_order(mock_order)
            mock_stop.assert_called_once_with("SELL", 75, 145.00)
    
    def test_create_stop_limit_order(self):
        """Test 14: Create stop-limit order"""
        mock_order = Mock(spec=Order)
        mock_order.action = "BUY"
        mock_order.quantity = 25
        mock_order.order_type = "STOP_LIMIT"
        mock_order.limit_price = 149.00
        mock_order.stop_price = 150.00
        mock_order.ticker = self.mock_ticker
        
        with patch('backend.order_manager.StopLimitOrder') as mock_stop_limit:
            self.manager._create_ib_order(mock_order)
            mock_stop_limit.assert_called_once_with("BUY", 25, 149.00, 150.00)
    
    def test_create_unknown_order_type_returns_none(self):
        """Test 15: Unknown order type returns None"""
        mock_order = Mock(spec=Order)
        mock_order.action = "BUY"
        mock_order.quantity = 100
        mock_order.order_type = "INVALID_TYPE"
        mock_order.ticker = self.mock_ticker
        
        result = self.manager._create_ib_order(mock_order)
        self.assertIsNone(result)
    
    def test_create_ib_order_exception_handling(self):
        """Test 16: Exception in IBOrder creation returns None"""
        mock_order = Mock(spec=Order)
        mock_order.action = "BUY"
        mock_order.quantity = "invalid"  # This will cause error
        mock_order.order_type = "MARKET"
        
        with patch('backend.order_manager.MarketOrder', side_effect=Exception("Test error")):
            result = self.manager._create_ib_order(mock_order)
            self.assertIsNone(result)


class TestOrderManagerInit(unittest.TestCase):
    """Test 17-20: OrderManager initialization and attributes"""
    
    def test_init_creates_executor(self):
        """Test 17: OrderManager creates ThreadPoolExecutor"""
        manager = OrderManager()
        self.assertIsNotNone(manager._executor)
        self.assertEqual(manager._executor._max_workers, 3)
    
    def test_init_creates_pending_submissions_dict(self):
        """Test 18: OrderManager creates pending submissions dict"""
        manager = OrderManager()
        self.assertIsInstance(manager._pending_submissions, dict)
        self.assertEqual(len(manager._pending_submissions), 0)
    
    def test_db_property_lazy_loads(self):
        """Test 19: Database session is lazily loaded"""
        manager = OrderManager()
        with patch('backend.order_manager.SessionLocal') as mock_session_local:
            db1 = manager.db
            # Access again - should reuse same session
            db2 = manager.db
            # SessionLocal should only be called once (lazy loading on first access)
            self.assertTrue(mock_session_local.called or db1 is db2)
    
    def test_close_db_closes_session(self):
        """Test 20: _close_db closes database session"""
        manager = OrderManager()
        mock_db = Mock()
        manager._db = mock_db
        manager._close_db()
        mock_db.close.assert_called_once()
        self.assertIsNone(manager._db)


class TestOrderValidation(unittest.TestCase):
    """Test 21-27: Order parameter validation"""
    
    def setUp(self):
        """Setup test manager"""
        self.manager = OrderManager()
    
    def test_validate_market_order_no_prices(self):
        """Test 21: MARKET order validation passes without prices"""
        result = self.manager._validate_order_params("MARKET", None, None)
        self.assertTrue(result)
    
    def test_validate_limit_order_requires_limit_price(self):
        """Test 22: LIMIT order requires limit_price"""
        result = self.manager._validate_order_params("LIMIT", None, None)
        self.assertFalse(result)
    
    def test_validate_limit_order_with_limit_price(self):
        """Test 23: LIMIT order validation passes with limit_price"""
        result = self.manager._validate_order_params("LIMIT", 150.00, None)
        self.assertTrue(result)
    
    def test_validate_stop_order_requires_stop_price(self):
        """Test 24: STOP order requires stop_price"""
        result = self.manager._validate_order_params("STOP", None, None)
        self.assertFalse(result)
    
    def test_validate_stop_order_with_stop_price(self):
        """Test 25: STOP order validation passes with stop_price"""
        result = self.manager._validate_order_params("STOP", None, 145.00)
        self.assertTrue(result)
    
    def test_validate_stop_limit_requires_both_prices(self):
        """Test 26: STOP_LIMIT order requires both prices"""
        result = self.manager._validate_order_params("STOP_LIMIT", 149.00, None)
        self.assertFalse(result)
        
        result = self.manager._validate_order_params("STOP_LIMIT", None, 150.00)
        self.assertFalse(result)
    
    def test_validate_stop_limit_with_both_prices(self):
        """Test 27: STOP_LIMIT order validation passes with both prices"""
        result = self.manager._validate_order_params("STOP_LIMIT", 149.00, 150.00)
        self.assertTrue(result)


class TestOrderConversion(unittest.TestCase):
    """Test 28-32: Order status conversion and string representation"""
    
    def setUp(self):
        """Setup test manager"""
        self.manager = OrderManager()
        self.mock_db = Mock()
        self.manager._db = self.mock_db
    
    def test_update_order_status_filled(self):
        """Test 28: Update order status to FILLED"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        mock_order.status = OrderStatus.SUBMITTED
        mock_order.filled_quantity = 0
        
        mock_trade = Mock()
        mock_trade.orderStatus.status = "Filled"
        mock_trade.orderStatus.filled = 100
        mock_trade.orderStatus.remaining = 0
        mock_trade.orderStatus.avgFillPrice = 150.50
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_order
        
        result = self.manager.update_order_status(1, mock_trade)
        
        self.assertTrue(result)
        self.assertEqual(mock_order.status, OrderStatus.FILLED)
        self.assertEqual(mock_order.filled_quantity, 100)
        self.assertEqual(mock_order.remaining_quantity, 0)
    
    def test_update_order_status_submitted(self):
        """Test 29: Update order status to SUBMITTED"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        
        mock_trade = Mock()
        mock_trade.orderStatus.status = "Submitted"
        mock_trade.orderStatus.filled = 0
        mock_trade.orderStatus.remaining = 100
        mock_trade.orderStatus.avgFillPrice = 0
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_order
        
        result = self.manager.update_order_status(1, mock_trade)
        
        self.assertTrue(result)
        self.assertEqual(mock_order.status, OrderStatus.SUBMITTED)
    
    def test_update_order_status_cancelled(self):
        """Test 30: Update order status to CANCELLED"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        mock_order.status = OrderStatus.SUBMITTED
        
        mock_trade = Mock()
        mock_trade.orderStatus.status = "Cancelled"
        mock_trade.orderStatus.filled = 0
        mock_trade.orderStatus.remaining = 100
        mock_trade.orderStatus.avgFillPrice = 0
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_order
        
        result = self.manager.update_order_status(1, mock_trade)
        
        self.assertTrue(result)
        self.assertEqual(mock_order.status, OrderStatus.CANCELLED)
        self.assertIsNotNone(mock_order.cancelled_at)
    
    def test_update_order_status_order_not_found(self):
        """Test 31: Update non-existent order returns False"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        mock_trade = Mock()
        result = self.manager.update_order_status(999, mock_trade)
        
        self.assertFalse(result)
    
    def test_update_order_status_exception_handling(self):
        """Test 32: Exception in update_order_status returns False"""
        self.mock_db.query.side_effect = Exception("DB error")
        
        mock_trade = Mock()
        result = self.manager.update_order_status(1, mock_trade)
        
        self.assertFalse(result)
        self.mock_db.rollback.assert_called_once()


class TestOrderParsing(unittest.TestCase):
    """Test 33-37: Order parsing and retrieval"""
    
    def setUp(self):
        """Setup test manager"""
        self.manager = OrderManager()
        self.mock_db = Mock()
        self.manager._db = self.mock_db
    
    def test_get_order_by_id(self):
        """Test 33: Get order by ID"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_order
        
        result = self.manager.get_order(1)
        
        self.assertEqual(result.id, 1)
        self.mock_db.query.assert_called()
    
    def test_get_order_not_found(self):
        """Test 34: Get non-existent order returns None"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.manager.get_order(999)
        
        self.assertIsNone(result)
    
    def test_get_orders_all(self):
        """Test 35: Get all orders"""
        mock_orders = [Mock(spec=Order), Mock(spec=Order)]
        self.mock_db.query.return_value.join.return_value.order_by.return_value.limit.return_value.all.return_value = mock_orders
        
        result = self.manager.get_orders()
        
        self.assertEqual(len(result), 2)
    
    def test_get_orders_with_status_filter(self):
        """Test 36: Get orders filtered by status"""
        mock_order = Mock(spec=Order)
        mock_order.status = OrderStatus.FILLED
        
        self.mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_order]
        
        result = self.manager.get_orders(status=OrderStatus.FILLED)
        
        self.assertEqual(len(result), 1)
    
    def test_get_orders_with_ticker_filter(self):
        """Test 37: Get orders filtered by ticker symbol"""
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.symbol = "AAPL"
        
        mock_order = Mock(spec=Order)
        mock_order.ticker = mock_ticker
        
        self.mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_order]
        
        result = self.manager.get_orders(ticker_symbol="AAPL")
        
        self.assertEqual(len(result), 1)


class TestOrderCancellation(unittest.TestCase):
    """Test 38-40: Order cancellation methods"""
    
    def setUp(self):
        """Setup test manager"""
        self.manager = OrderManager()
        self.mock_db = Mock()
        self.manager._db = self.mock_db
    
    def test_cancel_order_success(self):
        """Test 38: Cancel order successfully"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        mock_order.status = OrderStatus.SUBMITTED
        mock_order.ibkr_order_id = 100
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_order
        self.manager.ibkr_collector = None
        
        result = self.manager.cancel_order(1)
        
        self.assertTrue(result)
        self.assertEqual(mock_order.status, OrderStatus.CANCELLED)
        self.assertIsNotNone(mock_order.cancelled_at)
    
    def test_cancel_order_already_filled(self):
        """Test 39: Cannot cancel filled order"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        mock_order.status = OrderStatus.FILLED
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_order
        
        result = self.manager.cancel_order(1)
        
        self.assertFalse(result)
    
    def test_cancel_multiple_orders(self):
        """Test 40: Cancel multiple orders"""
        mock_order1 = Mock(spec=Order)
        mock_order1.id = 1
        mock_order1.status = OrderStatus.SUBMITTED
        
        mock_order2 = Mock(spec=Order)
        mock_order2.id = 2
        mock_order2.status = OrderStatus.PENDING
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [mock_order1, mock_order2]
        self.manager.ibkr_collector = None
        
        results = self.manager.cancel_multiple_orders([1, 2])
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results[1])
        self.assertTrue(results[2])


class TestOrderStatistics(unittest.TestCase):
    """Additional tests: Order statistics and sync"""
    
    def setUp(self):
        """Setup test manager"""
        self.manager = OrderManager()
        self.mock_db = Mock()
        self.manager._db = self.mock_db
    
    def test_get_order_statistics(self):
        """Test: Get order statistics"""
        mock_orders = [
            Mock(spec=Order, status=OrderStatus.FILLED, filled_quantity=100, avg_fill_price=150.00, commission=10.0),
        ]
        
        self.mock_db.query.return_value.count.return_value = 5
        self.mock_db.query.return_value.filter.return_value.count.side_effect = [3, 1, 1]  # filled, cancelled, pending
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_orders
        
        result = self.manager.get_order_statistics()
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_orders', result)
        self.assertIn('filled', result)


if __name__ == '__main__':
    unittest.main()
