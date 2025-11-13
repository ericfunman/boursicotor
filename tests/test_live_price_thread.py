"""
Unit tests for live price collection thread
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from backend.live_price_thread import (
    LivePriceCollector,
    start_live_price_collection,
    stop_live_price_collection,
    is_collecting,
    get_current_symbol,
)


class TestLivePriceCollector:
    """Test LivePriceCollector class"""

    def test_init(self):
        """Test LivePriceCollector initialization"""
        collector = LivePriceCollector()
        assert collector.thread is None
        assert collector.running is False
        assert collector.symbol is None
        assert collector.interval == 1
        assert collector.ib is None

    def test_start(self):
        """Test starting price collection"""
        collector = LivePriceCollector()
        with patch.object(collector, '_collect_prices'):
            result = collector.start("TTE", interval=1)
            assert result is True
            assert collector.running is True
            assert collector.symbol == "TTE"
            assert collector.interval == 1
            assert collector.thread is not None

    def test_start_already_running(self):
        """Test starting when already running"""
        collector = LivePriceCollector()
        collector.running = True
        collector.symbol = "TTE"
        result = collector.start("WLN", interval=1)
        assert result is False
        assert collector.symbol == "TTE"  # Should not change

    def test_stop(self):
        """Test stopping price collection"""
        collector = LivePriceCollector()
        collector.running = True
        collector.thread = Mock()
        result = collector.stop()
        assert result is True
        assert collector.running is False
        collector.thread.join.assert_called_once_with(timeout=5)

    def test_stop_not_running(self):
        """Test stopping when not running"""
        collector = LivePriceCollector()
        result = collector.stop()
        assert result is False

    @patch('backend.live_price_thread.SessionLocal')
    @patch('backend.live_price_thread.IB')
    def test_collect_prices_connection_success(self, mock_ib_class, mock_session_local):
        """Test successful connection in collect_prices"""
        # Setup mocks
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        mock_ib_instance = Mock()
        mock_ib_class.return_value = mock_ib_instance
        mock_ib_instance.isConnected.return_value = True
        
        # Setup bar data
        mock_bar = Mock()
        mock_bar.close = 56.15
        mock_bar.date = "2025-11-13 17:05:00+01:00"
        mock_ib_instance.reqHistoricalData.return_value = [mock_bar]
        
        collector = LivePriceCollector()
        collector.symbol = "TTE"
        collector.running = False  # Will stop immediately after first iteration
        
        # Should not raise any exceptions
        with patch.object(collector, '_save_price_to_db', return_value=True):
            collector._collect_prices()
        
        # Verify connection attempted
        mock_ib_instance.connect.assert_called_once_with('127.0.0.1', 4002, clientId=201)

    @patch('backend.live_price_thread.SessionLocal')
    @patch('backend.live_price_thread.IB')
    def test_collect_prices_connection_failure(self, mock_ib_class, mock_session_local):
        """Test connection failure in collect_prices"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        mock_ib_instance = Mock()
        mock_ib_class.return_value = mock_ib_instance
        mock_ib_instance.isConnected.return_value = False  # Connection fails
        
        collector = LivePriceCollector()
        collector.symbol = "TTE"
        
        # Should return without processing
        collector._collect_prices()
        
        # Verify disconnect was attempted
        mock_ib_instance.disconnect.assert_called()

    @patch('backend.live_price_thread.SessionLocal')
    def test_save_price_to_db_success(self, mock_session_local):
        """Test saving price to database successfully"""
        from backend.models import Ticker, HistoricalData
        
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        # Mock ticker query
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_ticker
        
        collector = LivePriceCollector()
        result = collector._save_price_to_db(mock_db, "TTE", 56.15)
        
        assert result is True
        # Verify add and commit were called
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @patch('backend.live_price_thread.SessionLocal')
    def test_save_price_to_db_no_ticker(self, mock_session_local):
        """Test saving price when ticker doesn't exist"""
        from backend.models import Ticker
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        collector = LivePriceCollector()
        result = collector._save_price_to_db(mock_db, "TTE", 56.15)
        
        assert result is True
        # Should create new ticker and save
        mock_db.add.assert_called()

    @patch('backend.live_price_thread.SessionLocal')
    def test_save_price_to_db_error(self, mock_session_local):
        """Test error handling in save_price_to_db"""
        mock_db = Mock()
        mock_db.query.side_effect = Exception("DB Error")
        
        collector = LivePriceCollector()
        result = collector._save_price_to_db(mock_db, "TTE", 56.15)
        
        assert result is False
        mock_db.rollback.assert_called_once()


class TestGlobalFunctions:
    """Test module-level functions"""

    def test_start_live_price_collection(self):
        """Test start_live_price_collection function"""
        with patch('backend.live_price_thread._live_collector.start', return_value=True) as mock_start:
            result = start_live_price_collection("TTE", interval=1)
            assert result is True
            mock_start.assert_called_once_with("TTE", 1)

    def test_stop_live_price_collection(self):
        """Test stop_live_price_collection function"""
        with patch('backend.live_price_thread._live_collector.stop', return_value=True) as mock_stop:
            result = stop_live_price_collection()
            assert result is True
            mock_stop.assert_called_once()

    def test_is_collecting_with_symbol(self):
        """Test is_collecting with specific symbol"""
        with patch('backend.live_price_thread._live_collector') as mock_collector:
            mock_collector.running = True
            mock_collector.symbol = "TTE"
            result = is_collecting("TTE")
            assert result is True

    def test_is_collecting_wrong_symbol(self):
        """Test is_collecting with wrong symbol"""
        with patch('backend.live_price_thread._live_collector') as mock_collector:
            mock_collector.running = True
            mock_collector.symbol = "TTE"
            result = is_collecting("WLN")
            assert result is False

    def test_is_collecting_without_symbol(self):
        """Test is_collecting without specific symbol"""
        with patch('backend.live_price_thread._live_collector') as mock_collector:
            mock_collector.running = True
            result = is_collecting()
            assert result is True

    def test_get_current_symbol_collecting(self):
        """Test get_current_symbol when collecting"""
        with patch('backend.live_price_thread._live_collector') as mock_collector:
            mock_collector.running = True
            mock_collector.symbol = "TTE"
            result = get_current_symbol()
            assert result == "TTE"

    def test_get_current_symbol_not_collecting(self):
        """Test get_current_symbol when not collecting"""
        with patch('backend.live_price_thread._live_collector') as mock_collector:
            mock_collector.running = False
            result = get_current_symbol()
            assert result is None
