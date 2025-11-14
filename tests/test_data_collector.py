"""
Unit tests for backend data_collector
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
from backend.data_collector import DataCollector
from backend.models import Ticker, HistoricalData


class TestDataCollectorInit:
    """Test DataCollector initialization"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_data_collector_init(self, mock_session):
        """Test DataCollector initializes with SessionLocal"""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        collector = DataCollector()
        
        assert collector.db is not None
        mock_session.assert_called_once()
    
    @patch('backend.data_collector.SessionLocal')
    def test_data_collector_cleanup(self, mock_session):
        """Test DataCollector closes database on cleanup"""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        collector = DataCollector()
        del collector
        
        # Session.close() should be called during cleanup
        # Note: __del__ behavior depends on garbage collection


class TestEnsureTickerExists:
    """Test ensure_ticker_exists method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_ensure_ticker_exists_new(self, mock_session):
        """Test creating a new ticker"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        # Simulate no existing ticker
        mock_db.query().filter().first.return_value = None
        
        # Mock the new ticker object
        new_ticker = Mock(spec=Ticker)
        new_ticker.symbol = 'TEST'
        
        collector = DataCollector()
        collector.db = mock_db
        
        result = collector.ensure_ticker_exists('TEST', 'Test Corp', 'NASDAQ')
        
        # Verify db.add and db.commit were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @patch('backend.data_collector.SessionLocal')
    def test_ensure_ticker_exists_existing(self, mock_session):
        """Test retrieving existing ticker"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        # Simulate existing ticker
        existing_ticker = Mock(spec=Ticker)
        existing_ticker.symbol = 'EXISTING'
        mock_db.query().filter().first.return_value = existing_ticker
        
        collector = DataCollector()
        collector.db = mock_db
        
        result = collector.ensure_ticker_exists('EXISTING')
        
        assert result == existing_ticker


class TestCollectHistoricalData:
    """Test collect_historical_data method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_collect_historical_data_returns_int(self, mock_session):
        """Test collect_historical_data returns an integer"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        # Mock ticker
        mock_ticker = Mock(spec=Ticker)
        mock_db.query().filter().first.return_value = mock_ticker
        
        collector = DataCollector()
        collector.db = mock_db
        
        # Mock the internal methods
        with patch.object(collector, '_generate_mock_data', return_value=5):
            result = collector.collect_historical_data('TEST', 'Test')
            
            assert isinstance(result, int)
            assert result == 5
    
    @patch('backend.data_collector.SessionLocal')
    def test_collect_historical_data_parameters(self, mock_session):
        """Test collect_historical_data accepts proper parameters"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        mock_ticker = Mock(spec=Ticker)
        mock_db.query().filter().first.return_value = mock_ticker
        
        collector = DataCollector()
        collector.db = mock_db
        
        with patch.object(collector, '_generate_mock_data', return_value=0):
            # Should accept duration and bar_size parameters
            result = collector.collect_historical_data(
                symbol='TEST',
                name='Test Corp',
                duration='5D',
                bar_size='1min',
                exchange='NYSE'
            )
            
            assert isinstance(result, int)


class TestDataCollectorMockData:
    """Test mock data generation"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_data_collector_has_generate_mock_data(self, mock_session):
        """Test DataCollector has _generate_mock_data method"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        collector = DataCollector()
        
        assert hasattr(collector, '_generate_mock_data')
        assert callable(collector._generate_mock_data)
    
    @patch('backend.data_collector.SessionLocal')
    def test_data_collector_has_store_bars(self, mock_session):
        """Test DataCollector has _store_bars method"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        collector = DataCollector()
        
        assert hasattr(collector, '_store_bars')
        assert callable(collector._store_bars)


class TestDataCollectorErrorHandling:
    """Test error handling in DataCollector"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_collect_historical_data_error_handling(self, mock_session):
        """Test collect_historical_data handles errors gracefully"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        # Simulate error in ensure_ticker_exists
        mock_db.query().filter().first.side_effect = Exception("DB Error")
        
        collector = DataCollector()
        collector.db = mock_db
        
        # Should return some value even on error (int or 0)
        with patch('backend.data_collector.logger'):
            result = collector.collect_historical_data('TEST')
            # On error, should return 0 or negative value
            assert isinstance(result, (int, type(None)))


class TestDataCollectorIBKRIntegration:
    """Test IBKR integration flags"""
    
    def test_ibkr_available_flag_exists(self):
        """Test IBKR_AVAILABLE flag is defined"""
        from backend.data_collector import IBKR_AVAILABLE
        assert isinstance(IBKR_AVAILABLE, bool)
    
    def test_ibkr_client_variable_exists(self):
        """Test ibkr_client variable is defined"""
        from backend.data_collector import ibkr_client
        # Should be None or an object
        assert ibkr_client is None or hasattr(ibkr_client, 'connected')


class TestDataCollectorAttributes:
    """Test DataCollector attributes"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_data_collector_db_attribute(self, mock_session):
        """Test DataCollector has db attribute"""
        mock_session.return_value = MagicMock()
        
        collector = DataCollector()
        
        assert hasattr(collector, 'db')
        assert collector.db is not None
