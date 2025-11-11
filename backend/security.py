"""
Security module for credential management and protection
"""
import os
from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages secure credential handling"""
    
    # IBKR Rate limiting: 100 requests per minute
    IBKR_RATE_LIMIT = 100
    IBKR_RATE_WINDOW = 60  # seconds
    
    # Session timeout: 30 minutes of inactivity
    SESSION_TIMEOUT = 30 * 60  # seconds
    
    # Max retries for operations
    MAX_RETRIES = 3
    
    def __init__(self):
        """Initialize credential manager"""
        self.credentials = {}
        self._validate_credentials()
    
    
    def _validate_credentials(self) -> None:
        """Validate that all required credentials are set"""
        required_vars = [
            'IBKR_HOST',
            'IBKR_PORT',
            'IBKR_CLIENT_ID'
        ]
        
        missing = []
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing.append(var)
            else:
                self.credentials[var] = value
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please check your .env file."
            )
        
        logger.info("✅ All credentials validated successfully")
    
    
    def get_ibkr_config(self) -> dict:
        """Get IBKR configuration"""
        return {
            'host': self.credentials.get('IBKR_HOST'),
            'port': int(self.credentials.get('IBKR_PORT', 7497)),
            'client_id': int(self.credentials.get('IBKR_CLIENT_ID', 1)),
        }
    
    
    @staticmethod
    def get_credential(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Safely get a credential from environment
        
        Args:
            key: Credential key
            default: Default value if not found
            
        Returns:
            Credential value or default
        """
        value = os.getenv(key, default)
        
        # Log access (but not the value!)
        logger.debug(f"Accessing credential: {key}")
        
        return value


class RateLimiter:
    """Rate limiting for IBKR API calls"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        import time
        
        now = time.time()
        # Remove old requests outside window
        self.requests = [t for t in self.requests if now - t < self.window_seconds]
        
        if len(self.requests) >= self.max_requests:
            logger.warning(
                f"⚠️ Rate limit reached: {len(self.requests)}/{self.max_requests} "
                f"requests in last {self.window_seconds}s"
            )
            return False
        
        self.requests.append(now)
        return True
    
    
    def get_wait_time(self) -> float:
        """Get how long to wait before next request allowed"""
        import time
        
        if len(self.requests) < self.max_requests:
            return 0
        
        oldest_request = min(self.requests)
        wait_time = oldest_request + self.window_seconds - time.time()
        return max(0, wait_time)


class SessionManager:
    """Manages session timeout and refresh"""
    
    def __init__(self, timeout_seconds: int = 30 * 60):
        """
        Initialize session manager
        
        Args:
            timeout_seconds: Session timeout in seconds
        """
        self.timeout_seconds = timeout_seconds
        self.last_activity = None
        self.is_active = False
    
    
    def start_session(self) -> None:
        """Start a new session"""
        import time
        self.last_activity = time.time()
        self.is_active = True
        logger.info("✅ Session started")
    
    
    def end_session(self) -> None:
        """End current session"""
        self.is_active = False
        self.last_activity = None
        logger.info("✅ Session ended")
    
    
    def refresh(self) -> None:
        """Refresh session activity timestamp"""
        import time
        self.last_activity = time.time()
    
    
    def is_valid(self) -> bool:
        """Check if session is still valid"""
        import time
        
        if not self.is_active or self.last_activity is None:
            return False
        
        elapsed = time.time() - self.last_activity
        if elapsed > self.timeout_seconds:
            logger.warning(
                f"⚠️ Session expired after {elapsed:.0f}s of inactivity"
            )
            self.end_session()
            return False
        
        return True


class SecurityValidator:
    """Validates security requirements"""
    
    @staticmethod
    def validate_order_parameters(
        ticker: str,
        action: str,
        quantity: int,
        order_type: str
    ) -> bool:
        """
        Validate order parameters for security
        
        Args:
            ticker: Stock ticker
            action: BUY or SELL
            quantity: Number of shares
            order_type: Order type (SMART, LIMIT, etc)
            
        Returns:
            True if valid, raises exception otherwise
        """
        # Validate ticker
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Invalid ticker")
        
        if len(ticker) > 10:
            raise ValueError("Ticker too long")
        
        # Validate action
        if action not in ['BUY', 'SELL']:
            raise ValueError(f"Invalid action: {action}")
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity} (must be positive integer)")
        
        if quantity > 1000000:  # Sanity check
            logger.warning(f"⚠️ Very large order quantity: {quantity}")
        
        # Validate order type
        valid_types = ['SMART', 'LIMIT', 'MARKET', 'STOP']
        if order_type not in valid_types:
            raise ValueError(f"Invalid order type: {order_type}")
        
        return True
    
    
    @staticmethod
    def validate_data_quality(df) -> bool:
        """
        Validate data quality and integrity
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid, raises exception otherwise
        """
        import pandas as pd
        
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Data must be a pandas DataFrame")
        
        # Check required columns
        required_cols = {'close', 'volume'}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Check for NaN values
        nan_count = df.isna().sum().sum()
        if nan_count > 0:
            logger.warning(f"⚠️ Data contains {nan_count} NaN values")
        
        # Check data integrity
        if 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
            invalid_rows = ~((df['high'] >= df['close']) & (df['close'] >= df['low']))
            if invalid_rows.any():
                raise ValueError("Data integrity error: high/low/close mismatch")
        
        # Calculate data quality
        total_cells = len(df) * len(df.columns)
        quality = 1.0 - (nan_count / total_cells)
        
        if quality < 0.95:
            logger.warning(f"⚠️ Data quality: {quality*100:.1f}%")
        
        return quality >= 0.90


# Module initialization
_credential_manager = None


def get_credential_manager() -> CredentialManager:
    """Get or create credential manager (singleton)"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager


def validate_startup() -> bool:
    """
    Validate security at application startup
    
    Returns:
        True if all checks pass
    """
    logger.info("🔒 Running security validation...")
    
    try:
        # Validate credentials
        _ = get_credential_manager()
        logger.info("✅ Credentials validated")
        
        # Check .env file permissions (if using local .env)
        env_file = Path('.env')
        if env_file.exists():
            import stat
            mode = os.stat(env_file).st_mode
            # Warn if world-readable
            if mode & stat.S_IROTH:
                logger.warning("⚠️ WARNING: .env file is world-readable!")
        
        logger.info("✅ Security validation passed")
        return True
    
    except Exception as e:
        logger.error(f"❌ Security validation failed: {e}")
        return False

