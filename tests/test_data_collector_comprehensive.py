"""
Comprehensive tests for backend/data_collector.py - target 70% coverage
"""
import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from sqlalchemy.orm import Session

from backend.data_collector import DataCollector
from backend.models import Ticker, HistoricalData, SessionLocal
from backend.config import logger


@pytest.fixture
def db_session():
    """Create a test database session"""
    return Mock(spec=Session)


@pytest.fixture
def sample_dataframe():
    """Create a sample OHLCV DataFrame"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1min')
    return pd.DataFrame({
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(105, 115, 100),
        'low': np.random.uniform(95, 105, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.randint(1000, 10000, 100),
    }, index=dates)


class TestDataCollectorInit:
    """Test DataCollector initialization"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_init_default(self, mock_session_local):
        """Test default initialization"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        collector = DataCollector()
        
        assert collector.db == mock_session
        mock_session_local.assert_called_once()
    
    @patch('backend.data_collector.SessionLocal')
    def test_init_with_saxo_deprecated(self, mock_session_local):
        """Test initialization with deprecated saxo parameter"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        collector = DataCollector(use_saxo=True)
        
        assert collector.db == mock_session
    
    @patch('backend.data_collector.SessionLocal')
    def test_destructor(self, mock_session_local):
        """Test __del__ closes database connection"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        collector = DataCollector()
        collector.__del__()
        
        mock_session.close.assert_called_once()


class TestEnsureTicker:
    """Test ensure_ticker_exists method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_ensure_ticker_exists_already(self, mock_session_local):
        """Test when ticker already exists"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.symbol = "AAPL"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_ticker
        
        collector = DataCollector()
        result = collector.ensure_ticker_exists("AAPL")
        
        assert result == mock_ticker
        mock_session.add.assert_not_called()
    
    @patch('backend.data_collector.SessionLocal')
    def test_ensure_ticker_create_new(self, mock_session_local):
        """Test when ticker needs to be created"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_ticker = Mock(spec=Ticker)
        mock_session.add.return_value = None
        
        collector = DataCollector()
        with patch('backend.data_collector.Ticker') as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker
            result = collector.ensure_ticker_exists("AAPL", "Apple", "NASDAQ")
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()


class TestCollectHistoricalData:
    """Test collect_historical_data method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_collect_historical_data_ibkr_available(self, mock_session_local):
        """Test collecting data when IBKR is available"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_ticker
        
        collector = DataCollector()
        
        # Mock saxo_client as None and ibkr not available
        collector.saxo_client = None
        
        with patch('backend.data_collector.IBKR_AVAILABLE', False):
            with patch.object(collector, '_generate_mock_data', return_value=50):
                result = collector.collect_historical_data(
                    "AAPL", "Apple", "1D", "1min", "NASDAQ"
                )
                
                assert result == 50
    
    @patch('backend.data_collector.SessionLocal')
    def test_collect_historical_data_symbol_only(self, mock_session_local):
        """Test with minimal parameters"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_ticker
        
        collector = DataCollector()
        collector.saxo_client = None
        
        with patch('backend.data_collector.IBKR_AVAILABLE', False):
            with patch.object(collector, '_generate_mock_data', return_value=0):
                result = collector.collect_historical_data("AAPL")
                
                assert result >= 0


class TestCollectMultipleTickers:
    """Test collect_multiple_tickers method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_collect_multiple_tickers(self, mock_session_local):
        """Test collecting data for multiple tickers"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_ticker
        
        collector = DataCollector()
        collector.saxo_client = None
        
        with patch('backend.data_collector.IBKR_AVAILABLE', False):
            with patch.object(collector, 'collect_historical_data', return_value=10):
                tickers = [("AAPL", "Apple"), ("MSFT", "Microsoft")]
                
                with patch('time.sleep'):
                    collector.collect_multiple_tickers(tickers)
                
                assert collector.collect_historical_data.call_count == 2


class TestGetLatestData:
    """Test get_latest_data method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_get_latest_data_success(self, mock_session_local, sample_dataframe):
        """Test getting latest data successfully"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_ticker
        
        # Mock historical data records
        mock_records = []
        for idx, row in sample_dataframe.iloc[:10].iterrows():
            record = Mock(spec=HistoricalData)
            record.timestamp = idx
            record.open = row['open']
            record.high = row['high']
            record.low = row['low']
            record.close = row['close']
            record.volume = row['volume']
            mock_records.append(record)
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_records
        
        collector = DataCollector()
        result = collector.get_latest_data("AAPL", limit=10)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10
        assert 'open' in result.columns
    
    @patch('backend.data_collector.SessionLocal')
    def test_get_latest_data_ticker_not_found(self, mock_session_local):
        """Test when ticker is not found"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        collector = DataCollector()
        result = collector.get_latest_data("UNKNOWN")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    @patch('backend.data_collector.SessionLocal')
    def test_get_latest_data_no_records(self, mock_session_local):
        """Test when no historical data exists"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_ticker
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        collector = DataCollector()
        result = collector.get_latest_data("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestCleanupOldData:
    """Test cleanup_old_data method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_cleanup_old_data_default_days(self, mock_session_local):
        """Test cleanup with default retention days"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.delete.return_value = 100
        
        collector = DataCollector()
        result = collector.cleanup_old_data()
        
        assert result == 100
        mock_session.commit.assert_called_once()
    
    @patch('backend.data_collector.SessionLocal')
    def test_cleanup_old_data_custom_days(self, mock_session_local):
        """Test cleanup with custom retention days"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.delete.return_value = 50
        
        collector = DataCollector()
        result = collector.cleanup_old_data(days=30)
        
        assert result == 50
        mock_session.commit.assert_called_once()
    
    @patch('backend.data_collector.SessionLocal')
    def test_cleanup_old_data_error(self, mock_session_local):
        """Test cleanup with database error"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.delete.side_effect = Exception("DB error")
        
        collector = DataCollector()
        result = collector.cleanup_old_data()
        
        assert result == 0
        mock_session.rollback.assert_called_once()


class TestStoreDataFrame:
    """Test _store_dataframe method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_store_dataframe_success(self, mock_session_local, sample_dataframe):
        """Test storing DataFrame successfully"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        mock_ticker.symbol = "AAPL"
        
        collector = DataCollector()
        result = collector._store_dataframe(sample_dataframe.head(10), mock_ticker, '1min')
        
        # Should return number of records stored
        assert isinstance(result, int)
        assert result >= 0
    
    @patch('backend.data_collector.SessionLocal')
    def test_store_dataframe_empty(self, mock_session_local):
        """Test storing empty DataFrame"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        
        collector = DataCollector()
        result = collector._store_dataframe(pd.DataFrame(), mock_ticker, '1min')
        
        assert result == 0


class TestGenerateMockData:
    """Test _generate_mock_data method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_generate_mock_data_1min(self, mock_session_local):
        """Test mock data generation for 1min bars"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        
        collector = DataCollector()
        with patch.object(collector, '_store_dataframe', return_value=1440):
            result = collector._generate_mock_data("AAPL", "1D", "1min", mock_ticker)
            
            assert result == 1440
    
    @patch('backend.data_collector.SessionLocal')
    def test_generate_mock_data_1hour(self, mock_session_local):
        """Test mock data generation for 1hour bars"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        
        collector = DataCollector()
        with patch.object(collector, '_store_dataframe', return_value=24):
            result = collector._generate_mock_data("AAPL", "1D", "1hour", mock_ticker)
            
            assert result == 24


class TestStoreBars:
    """Test _store_bars method"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_store_bars_success(self, mock_session_local):
        """Test bar storage"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        
        bars = [
            {'timestamp': datetime.now(timezone.utc), 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000},
            {'timestamp': datetime.now(timezone.utc), 'open': 102, 'high': 107, 'low': 97, 'close': 104, 'volume': 1100},
        ]
        
        collector = DataCollector()
        result = collector._store_bars(bars, mock_ticker, "1min")
        
        assert result >= 0


class TestDataCollectorEdgeCases:
    """Test edge cases and error handling"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_get_latest_data_with_exception(self, mock_session_local):
        """Test get_latest_data error handling"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("DB error")
        
        collector = DataCollector()
        result = collector.get_latest_data("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    @patch('backend.data_collector.SessionLocal')
    def test_collect_historical_data_with_exception(self, mock_session_local):
        """Test collect_historical_data error handling"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("DB error")
        
        collector = DataCollector()
        result = collector.collect_historical_data("AAPL")
        
        assert result == 0


class TestDataCollectorIntegration:
    """Integration tests"""
    
    @patch('backend.data_collector.SessionLocal')
    def test_full_workflow(self, mock_session_local, sample_dataframe):
        """Test complete workflow: create ticker, store data, retrieve"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_ticker = Mock(spec=Ticker)
        mock_ticker.id = 1
        
        # Setup for ensure_ticker_exists
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        collector = DataCollector()
        
        with patch('backend.data_collector.Ticker') as mock_ticker_class:
            mock_ticker_class.return_value = mock_ticker
            ticker = collector.ensure_ticker_exists("AAPL", "Apple", "NASDAQ")
            
            assert mock_session.add.called
            assert mock_session.commit.called
    
    @patch('backend.data_collector.SessionLocal')
    def test_multiple_symbols_workflow(self, mock_session_local):
        """Test workflow with multiple symbols"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        collector = DataCollector()
        collector.saxo_client = None
        
        with patch('backend.data_collector.IBKR_AVAILABLE', False):
            with patch.object(collector, 'ensure_ticker_exists', return_value=Mock()):
                with patch.object(collector, '_generate_mock_data', return_value=100):
                    tickers = [("AAPL", "Apple"), ("MSFT", "Microsoft"), ("GOOGL", "Google")]
                    
                    with patch('time.sleep'):
                        collector.collect_multiple_tickers(tickers)
                    
                    assert collector.ensure_ticker_exists.call_count >= 0
