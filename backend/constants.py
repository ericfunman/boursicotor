"""
Application-wide constants
Extracted from duplicated strings in codebase
"""

# DataFrame column names (used heavily in data processing)
CONST_TIMESTAMP = "timestamp"
CONST_CHUNK_DAYS = "chunk_days"
CONST_HIGH = "high"
CONST_LOW = "low"
CONST_OPEN = "open"
CONST_CLOSE = "close"
CONST_VOLUME = "volume"
CONST_NAME = "name"
CONST_SUCCESS = "success"
CONST_EXCHANGE = "exchange"
CONST_CURRENCY = "currency"
CONST_ISIN = "isin"

# Time intervals
CONST_1MIN = "1min"
CONST_5MIN = "5min"
CONST_15MIN = "15min"
CONST_30MIN = "30min"
CONST_1HOUR = "1h"
CONST_1DAY = "1d"
CONST_1WEEK = "1w"
CONST_1MONTH = "1M"

# Status values
STATUS_ACTIVE = "ACTIVE"
STATUS_INACTIVE = "INACTIVE"
STATUS_PENDING = "PENDING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_FILLED = "FILLED"
STATUS_CANCELLED = "CANCELLED"
STATUS_REJECTED = "REJECTED"

# Order actions
ACTION_BUY = "BUY"
ACTION_SELL = "SELL"

# Order types
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_STOP = "STOP"
ORDER_TYPE_STOP_LIMIT = "STOP_LIMIT"

# Default configurations
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BATCH_SIZE = 1000
DEFAULT_CHUNK_SIZE = 5000

# Error messages
ERROR_DATABASE_CONNECTION = "Database connection failed"
ERROR_INVALID_PARAMETER = "Invalid parameter"
ERROR_TIMEOUT = "Operation timeout"
ERROR_AUTHENTICATION = "Authentication failed"
ERROR_NOT_FOUND = "Resource not found"
ERROR_PERMISSION_DENIED = "Permission denied"

# Database foreign keys (S1192)
FK_TICKERS_ID = "tickers.id"
FK_STRATEGIES_ID = "strategies.id"

# IBKR connection messages (S1192)
MSG_IBKR_NOT_CONNECTED = "❌ Pas connecté à IBKR"
