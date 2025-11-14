"""
Tests for backend/models.py
Target: Complete coverage of utility functions and models
"""
import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from backend.models import (
    datetime_paris, format_datetime_paris,
    OrderStatus, AutoTraderStatus,
    SessionLocal, Base, engine
)


class TestDateTimeUtilities:
    """Test datetime conversion and formatting utilities"""
    
    def test_datetime_paris_with_utc_datetime(self):
        """Test converting UTC datetime to Paris timezone"""
        utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        paris_dt = datetime_paris(utc_dt)
        
        assert paris_dt is not None
        assert paris_dt.tzinfo == ZoneInfo('Europe/Paris')
        # Paris is UTC+1 in winter
        assert paris_dt.hour == 13
        
    def test_datetime_paris_with_naive_datetime(self):
        """Test converting naive datetime (assumes UTC)"""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)
        paris_dt = datetime_paris(naive_dt)
        
        assert paris_dt is not None
        assert paris_dt.tzinfo == ZoneInfo('Europe/Paris')
        # Should interpret as UTC and convert
        assert paris_dt.hour == 13
        
    def test_datetime_paris_with_none(self):
        """Test datetime_paris with None input"""
        result = datetime_paris(None)
        assert result is None
        
    def test_format_datetime_paris_with_utc(self):
        """Test formatting UTC datetime in Paris timezone"""
        utc_dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=ZoneInfo('UTC'))
        formatted = format_datetime_paris(utc_dt)
        
        assert '2024-01-15' in formatted
        assert '13:30:45' in formatted  # UTC+1 in winter
        
    def test_format_datetime_paris_with_naive(self):
        """Test formatting naive datetime (assumes UTC)"""
        naive_dt = datetime(2024, 1, 15, 12, 30, 45)
        formatted = format_datetime_paris(naive_dt)
        
        assert '2024-01-15' in formatted
        assert '13:30:45' in formatted
        
    def test_format_datetime_paris_with_none(self):
        """Test format_datetime_paris with None input"""
        formatted = format_datetime_paris(None)
        assert formatted == "N/A"
        
    def test_format_datetime_paris_custom_format(self):
        """Test custom format string"""
        utc_dt = datetime(2024, 1, 15, 12, 30, tzinfo=ZoneInfo('UTC'))
        formatted = format_datetime_paris(utc_dt, fmt='%Y/%m/%d')
        
        assert formatted == '2024/01/15'
        
    def test_format_datetime_paris_summer_time(self):
        """Test Paris timezone conversion during summer (UTC+2)"""
        # July 15 - summer time in Paris (UTC+2)
        utc_dt = datetime(2024, 7, 15, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        paris_dt = datetime_paris(utc_dt)
        
        assert paris_dt.hour == 14  # UTC+2 in summer


class TestEnums:
    """Test enum classes"""
    
    def test_order_status_enum_values(self):
        """Test OrderStatus enum has expected values"""
        assert hasattr(OrderStatus, 'PENDING')
        assert hasattr(OrderStatus, 'SUBMITTED')
        assert hasattr(OrderStatus, 'FILLED')
        assert hasattr(OrderStatus, 'CANCELLED')
        assert hasattr(OrderStatus, 'REJECTED')
        
    def test_auto_trader_status_enum_values(self):
        """Test AutoTraderStatus enum has expected values"""
        assert hasattr(AutoTraderStatus, 'RUNNING')
        assert hasattr(AutoTraderStatus, 'STOPPED')
        assert hasattr(AutoTraderStatus, 'PAUSED')
        assert hasattr(AutoTraderStatus, 'ERROR')


class TestDatabaseSession:
    """Test database session and engine configuration"""
    
    def test_session_local_creates_session(self):
        """Test that SessionLocal creates a valid session"""
        session = SessionLocal()
        assert session is not None
        session.close()
        
    def test_engine_is_configured(self):
        """Test that engine is properly configured"""
        assert engine is not None
        assert engine.url is not None
        
    def test_base_has_metadata(self):
        """Test that Base has metadata"""
        assert Base.metadata is not None
        assert hasattr(Base.metadata, 'tables')


class TestModels:
    """Test model classes and their relationships"""
    
    def test_ticker_model_exists(self):
        """Test Ticker model is defined"""
        from backend.models import Ticker
        assert Ticker is not None
        assert hasattr(Ticker, '__tablename__')
        
    def test_strategy_model_exists(self):
        """Test Strategy model is defined"""
        from backend.models import Strategy
        assert Strategy is not None
        assert hasattr(Strategy, '__tablename__')
        
    def test_historical_data_model_exists(self):
        """Test HistoricalData model is defined"""
        from backend.models import HistoricalData
        assert HistoricalData is not None
        assert hasattr(HistoricalData, '__tablename__')
        
    def test_backtest_model_exists(self):
        """Test Backtest model is defined"""
        from backend.models import Backtest
        assert Backtest is not None
        assert hasattr(Backtest, '__tablename__')
        
    def test_order_model_exists(self):
        """Test Order model is defined"""
        from backend.models import Order
        assert Order is not None
        assert hasattr(Order, '__tablename__')
        
    def test_trade_model_exists(self):
        """Test Trade model is defined"""
        from backend.models import Trade
        assert Trade is not None
        assert hasattr(Trade, '__tablename__')
        
    def test_auto_trader_session_model_exists(self):
        """Test AutoTraderSession model is defined"""
        from backend.models import AutoTraderSession
        assert AutoTraderSession is not None
        assert hasattr(AutoTraderSession, '__tablename__')
        
    def test_job_model_exists(self):
        """Test DataCollectionJob model is defined"""
        from backend.models import DataCollectionJob
        assert DataCollectionJob is not None
        assert hasattr(DataCollectionJob, '__tablename__')


class TestModelRelationships:
    """Test that model relationships are defined"""
    
    def test_ticker_has_historical_data_relationship(self):
        """Test Ticker has relationship to HistoricalData"""
        from backend.models import Ticker
        assert hasattr(Ticker, 'historical_data')
        
    def test_ticker_has_trades_relationship(self):
        """Test Ticker has relationship to Trades"""
        from backend.models import Ticker
        assert hasattr(Ticker, 'trades')
        
    def test_strategy_has_backtests_relationship(self):
        """Test Strategy has relationship to Backtests"""
        from backend.models import Strategy
        assert hasattr(Strategy, 'backtests')
        
    def test_order_has_ticker_relationship(self):
        """Test Order has relationship to Ticker"""
        from backend.models import Order
        assert hasattr(Order, 'ticker')


class TestModelCreation:
    """Test creating model instances"""
    
    def test_create_ticker_instance(self):
        """Test creating a Ticker instance"""
        from backend.models import Ticker
        ticker = Ticker(
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ',
            currency='USD'
        )
        assert ticker.symbol == 'AAPL'
        assert ticker.name == 'Apple Inc.'
        
    def test_create_strategy_instance(self):
        """Test creating a Strategy instance"""
        from backend.models import Strategy
        strategy = Strategy(
            name='Test Strategy',
            strategy_type='simple_ma',
            parameters='{"sma_period": 20}'
        )
        assert strategy.name == 'Test Strategy'
        assert strategy.strategy_type == 'simple_ma'
        
    def test_create_order_instance(self):
        """Test creating an Order instance"""
        from backend.models import Order
        order = Order(
            ticker_id=1,
            action='BUY',
            order_type='MARKET',
            quantity=100,
            status=OrderStatus.PENDING
        )
        assert order.action == 'BUY'
        assert order.quantity == 100
        assert order.status == OrderStatus.PENDING


class TestDatabaseConnection:
    """Test database connection and configuration"""
    
    def test_session_local_exists(self):
        """Test SessionLocal is properly configured"""
        assert SessionLocal is not None
        # Should be able to create a session
        session = SessionLocal()
        session.close()
    
    def test_get_db_generator(self):
        """Test get_db is a generator function"""
        from backend.models import get_db
        
        gen = get_db()
        # Should be a generator
        assert hasattr(gen, '__iter__')
        assert hasattr(gen, '__next__')
    
    def test_engine_exists(self):
        """Test engine is configured"""
        assert engine is not None


class TestEnumTypes:
    """Test enum fields in models"""
    
    def test_order_status_enum_values(self):
        """Test OrderStatus enum has expected values"""
        from backend.models import OrderStatus
        
        # Check common status values exist
        assert hasattr(OrderStatus, 'PENDING')
        assert hasattr(OrderStatus, 'FILLED')
    
    def test_auto_trader_status_enum_values(self):
        """Test AutoTraderStatus enum has expected values"""
        from backend.models import AutoTraderStatus
        
        # Check status values exist
        assert hasattr(AutoTraderStatus, 'RUNNING')


class TestTickerModel:
    """Test Ticker model"""
    
    def test_ticker_fields(self):
        """Test Ticker has expected fields"""
        from backend.models import Ticker
        
        ticker = Ticker(
            symbol='TEST',
            name='Test Company',
            exchange='TEST',
            currency='EUR'
        )
        
        assert ticker.symbol == 'TEST'
        assert ticker.name == 'Test Company'
        assert ticker.exchange == 'TEST'
        assert ticker.currency == 'EUR'
    
    def test_ticker_is_active_default(self):
        """Test Ticker is_active can be set"""
        from backend.models import Ticker
        
        ticker = Ticker(
            symbol='TEST',
            name='Test',
            exchange='TEST',
            currency='EUR',
            is_active=True
        )
        
        assert ticker.is_active is True


class TestHistoricalDataModel:
    """Test HistoricalData model"""
    
    def test_historical_data_fields(self):
        """Test HistoricalData has expected fields"""
        from backend.models import HistoricalData
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        data = HistoricalData(
            ticker_id=1,
            timestamp=now,
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.5,
            volume=1000000,
            interval='1day'
        )
        
        assert data.ticker_id == 1
        assert data.timestamp == now
        assert data.open == 100.0
        assert data.close == 102.5
    
    def test_historical_data_precision(self):
        """Test HistoricalData stores prices with precision"""
        from backend.models import HistoricalData
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        price = 56.045
        data = HistoricalData(
            ticker_id=1,
            timestamp=now,
            close=price,
            interval='1day'
        )
        
        assert data.close == price
