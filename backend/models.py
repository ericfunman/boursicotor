"""
Database models and connection management
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Index, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import enum
from backend.config import DATABASE_URL, logger
from backend.constants import FK_TICKERS_ID, FK_STRATEGIES_ID
from zoneinfo import ZoneInfo

from typing import Optional

Base = declarative_base()

# Timezone definitions
PARIS_TZ = ZoneInfo('Europe/Paris')
UTC_TZ = ZoneInfo('UTC')

def datetime_paris(dt: datetime) -> Optional[datetime]:
    """Convert UTC datetime to Europe/Paris timezone"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(PARIS_TZ)

def format_datetime_paris(dt: datetime, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime in Europe/Paris timezone
    
    NOTE: This always assumes input is UTC if naive
    """
    if dt is None:
        return "N/A"
    
    # Force interpretation as UTC if naive (don't rely on tzinfo)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    
    # Always convert to Paris time
    paris_dt = dt.astimezone(PARIS_TZ)
    return paris_dt.strftime(fmt)

# Create engine with database-specific optimizations
if DATABASE_URL.startswith("sqlite://"):
    # SQLite-specific configuration to handle concurrent access
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"timeout": 30, "check_same_thread": False},  # 30s timeout for locks, allow cross-thread
        poolclass=StaticPool,  # Use static pool for SQLite
        isolation_level="SERIALIZABLE"
    )
    
    # Enable WAL mode for better concurrent access
    def on_connect(dbapi_conn, connection_record):
        """TODO: Add docstring."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
        cursor.execute("PRAGMA cache_size=10000")  # Increase cache
        cursor.close()
    
    from sqlalchemy import event
    event.listen(engine, "connect", on_connect)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Ticker(Base):
    """Stock ticker information"""
    __tablename__ = "tickers"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    isin = Column(String(12), unique=True, nullable=True, index=True)  # ISIN code for faster lookups
    name = Column(String(100), nullable=False)
    exchange = Column(String(50), default="EURONEXT")
    currency = Column(String(3), default="EUR")
    sector = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=datetime.utcnow)
    
    # Relationships
    historical_data = relationship("HistoricalData", back_populates="ticker", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="ticker")


class JobStatus(enum.Enum):
    """Data collection job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataCollectionJob(Base):
    """Asynchronous data collection job tracking"""
    __tablename__ = "data_collection_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Job identification
    celery_task_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Job parameters
    ticker_symbol = Column(String(10), nullable=False, index=True)
    ticker_name = Column(String(100))
    source = Column(String(50), nullable=False)  # 'ibkr' only
    duration = Column(String(20))  # e.g., '1 M', '3 M'
    interval = Column(String(20))  # e.g., '5 secs', '1 min'
    
    # Job status
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(200))  # Current operation description
    
    # Results
    records_new = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_total = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Metadata
    created_by = Column(String(100))  # Future: user tracking
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_ticker_status', 'ticker_symbol', 'status'),
    )


class HistoricalData(Base):
    """Historical price data"""
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey(FK_TICKERS_ID), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    interval = Column(String(10), default="1min")  # 1min, 5min, 1hour, etc.
    
    # Technical indicators (computed and stored)
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_hist = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    ticker = relationship("Ticker", back_populates="historical_data")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ticker_timestamp', 'ticker_id', 'timestamp'),
        Index('idx_ticker_interval_timestamp', 'ticker_id', 'interval', 'timestamp'),
    )


class Strategy(Base):
    """Trading strategies"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    strategy_type = Column(String(50))  # momentum, mean_reversion, ml_based, etc.
    parameters = Column(Text)  # JSON string of parameters
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=datetime.utcnow)
    
    # Relationships
    backtests = relationship("Backtest", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")


class Backtest(Base):
    """Backtest results"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey(FK_STRATEGIES_ID), nullable=False, index=True)
    ticker_id = Column(Integer, ForeignKey(FK_TICKERS_ID), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    profit_factor = Column(Float)
    results_json = Column(Text)  # Detailed results as JSON
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")


class OrderStatus(enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ERROR = "error"


class Order(Base):
    """Live trading orders"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Order identification
    ibkr_order_id = Column(Integer, unique=True, index=True)  # IBKR's order ID
    perm_id = Column(Integer)  # IBKR's permanent order ID
    
    # Order details
    ticker_id = Column(Integer, ForeignKey(FK_TICKERS_ID), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey(FK_STRATEGIES_ID), index=True)
    
    # Order parameters
    action = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP, STOP_LIMIT
    quantity = Column(Integer, nullable=False)
    limit_price = Column(Float)  # For LIMIT and STOP_LIMIT orders
    stop_price = Column(Float)  # For STOP and STOP_LIMIT orders
    
    # Execution details
    filled_quantity = Column(Integer, default=0)
    remaining_quantity = Column(Integer)
    avg_fill_price = Column(Float)
    commission = Column(Float, default=0.0)
    
    # Status tracking
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    status_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    submitted_at = Column(DateTime)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Additional info
    is_paper_trade = Column(Boolean, default=True)
    notes = Column(Text)
    parent_order_id = Column(Integer, ForeignKey("orders.id"))  # For bracket orders
    
    # Relationships
    ticker = relationship("Ticker")
    strategy = relationship("Strategy")
    # Note: child_orders relationship removed to avoid circular import issues
    # Use direct queries for parent/child relationships if needed
    
    # Indexes
    __table_args__ = (
        Index('idx_order_status_created', 'status', 'created_at'),
        Index('idx_order_ticker_status', 'ticker_id', 'status'),
    )


class Trade(Base):
    """Trade execution records"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey(FK_TICKERS_ID), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey(FK_STRATEGIES_ID), index=True)
    order_type = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    entry_time = Column(DateTime, nullable=False, index=True)
    exit_time = Column(DateTime)
    pnl = Column(Float)
    pnl_percent = Column(Float)
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, CANCELLED
    is_paper_trade = Column(Boolean, default=True)
    commission = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    ticker = relationship("Ticker", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")


class AutoTraderStatus(enum.Enum):
    """Auto trader session status"""
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"


class AutoTraderSession(Base):
    """Auto trading session tracking"""
    __tablename__ = "auto_trader_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey(FK_TICKERS_ID), nullable=False)
    strategy_id = Column(Integer, ForeignKey(FK_STRATEGIES_ID), nullable=False)
    
    status = Column(Enum(AutoTraderStatus), default=AutoTraderStatus.STOPPED, nullable=False)
    
    # Configuration
    polling_interval = Column(Integer, default=60)  # seconds between data fetch
    max_position_size = Column(Integer, default=100)  # max shares per position
    max_daily_trades = Column(Integer, default=10)  # max trades per day
    stop_loss_pct = Column(Float, default=2.0)  # stop loss percentage
    take_profit_pct = Column(Float, default=5.0)  # take profit percentage
    
    # Session info
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    last_check_at = Column(DateTime)  # last time we checked for signals
    
    # Performance tracking
    total_orders = Column(Integer, default=0)
    successful_orders = Column(Integer, default=0)
    failed_orders = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    
    # Current state
    current_position = Column(Integer, default=0)  # current shares held
    last_signal = Column(String(10))  # BUY, SELL, HOLD
    last_signal_at = Column(DateTime)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    # NOTE: Cascade delete not appropriate for many-to-one relationships
    # Instead, use the cleanup script to remove orphaned sessions
    ticker = relationship("Ticker")
    strategy = relationship("Strategy")
    
    __table_args__ = (
        Index('idx_auto_trader_status', 'status'),
        Index('idx_auto_trader_ticker_strategy', 'ticker_id', 'strategy_id'),
    )


class MLModel(Base):
    """Machine Learning models metadata"""
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # LSTM, XGBoost, RandomForest, etc.
    version = Column(String(20), nullable=False)
    file_path = Column(String(255), nullable=False)
    training_start_date = Column(DateTime)
    training_end_date = Column(DateTime)
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    parameters = Column(Text)  # JSON string
    feature_importance = Column(Text)  # JSON string
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    trained_at = Column(DateTime)


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_db():
    """Drop all database tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


if __name__ == "__main__":
    init_db()
