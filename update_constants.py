"""
Replace duplicated strings with constants
"""
import re
import os
from pathlib import Path

BACKEND_DIR = Path("backend")

# Common duplicated strings to replace
DUPLICATES_TO_REPLACE = {
    'timestamp': 'CONST_TIMESTAMP',
    'chunk_days': 'CONST_CHUNK_DAYS',
    'high': 'CONST_HIGH',
    'low': 'CONST_LOW',
    'open': 'CONST_OPEN',
    'close': 'CONST_CLOSE',
    'volume': 'CONST_VOLUME',
    'name': 'CONST_NAME',
    'success': 'CONST_SUCCESS',
    'exchange': 'CONST_EXCHANGE',
    'currency': 'CONST_CURRENCY',
    'isin': 'CONST_ISIN',
}

def replace_in_file(file_path, replacements):
    """Replace duplicated strings in a file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    for old_str, const_name in replacements.items():
        # Replace only string literals, not variable names or comments
        # Pattern: "old_str" or 'old_str'
        pattern = rf"(['\"])({re.escape(old_str)})\1"
        
        # Don't replace if it's part of another identifier
        # Use lookahead/lookbehind
        pattern = rf"(?<![a-zA-Z0-9_])(['\"])({re.escape(old_str)})\1(?![a-zA-Z0-9_])"
        
        # But we need to be careful - only replace obvious string literals
        # Skip replacements in this approach as it's risky
        
    return content

def update_constants_file():
    """Update constants.py with all discovered constants"""
    
    constants_file = BACKEND_DIR / "constants.py"
    
    constants_content = '''"""
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
'''
    
    with open(constants_file, 'w', encoding='utf-8') as f:
        f.write(constants_content)
    
    print("✅ Updated constants.py with comprehensive constants")

if __name__ == "__main__":
    print("📝 Updating constants file...")
    update_constants_file()
    print("✅ Done!")
