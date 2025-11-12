"""
Security tests
"""
import pytest
import os
from unittest.mock import patch, MagicMock
import pandas as pd


class TestCredentialManager:
    """Test credential management"""
    
    def test_credential_manager_validates_required_vars(self):
        """Test that credential manager validates required environment variables"""
        from backend.security import CredentialManager
        
        # Mock missing env vars
        with patch.dict(os.environ, {'IBKR_HOST': '', 'IBKR_PORT': '', 'IBKR_CLIENT_ID': ''}):
            with pytest.raises(ValueError, match="Missing required environment variables"):
                CredentialManager()
    
    
    def test_credential_manager_loads_config(self):
        """Test that credential manager loads IBKR config"""
        from backend.security import CredentialManager
        
        with patch.dict(os.environ, {
            'IBKR_HOST': '127.0.0.1',
            'IBKR_PORT': '7497',
            'IBKR_CLIENT_ID': '1'
        }):
            manager = CredentialManager()
            config = manager.get_ibkr_config()
            
            assert config['host'] == '127.0.0.1'
            assert config['port'] == 7497
            assert config['client_id'] == 1
    
    
    def test_get_credential_safely(self):
        """Test safe credential retrieval"""
        from backend.security import CredentialManager
        
        with patch.dict(os.environ, {'TEST_KEY': 'test_value'}):
            value = CredentialManager.get_credential('TEST_KEY')
            assert value == 'test_value'
    
    
    def test_get_credential_with_default(self):
        """Test credential retrieval with default value"""
        from backend.security import CredentialManager
        
        with patch.dict(os.environ, {}, clear=True):
            value = CredentialManager.get_credential('NONEXISTENT', 'default_value')
            assert value == 'default_value'


class TestRateLimiter:
    """Test rate limiting"""
    
    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that rate limiter allows requests within limit"""
        from backend.security import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # Should allow 10 requests
        for i in range(10):
            assert limiter.is_allowed() is True
    
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test that rate limiter blocks requests over limit"""
        from backend.security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Allow 5 requests
        for i in range(5):
            assert limiter.is_allowed() is True
        
        # Block 6th request
        assert limiter.is_allowed() is False
    
    
    def test_rate_limiter_wait_time(self):
        """Test rate limiter reports correct wait time"""
        from backend.security import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Use both slots
        limiter.is_allowed()
        limiter.is_allowed()
        
        # Should report wait time > 0
        wait_time = limiter.get_wait_time()
        assert wait_time > 0
        assert wait_time <= 1.0


class TestSessionManager:
    """Test session management"""
    
    def test_session_manager_starts_session(self):
        """Test that session manager can start session"""
        from backend.security import SessionManager
        
        manager = SessionManager(timeout_seconds=60)
        manager.start_session()
        
        assert manager.is_active is True
        assert manager.last_activity is not None
    
    
    def test_session_manager_validates_active_session(self):
        """Test that session manager validates active session"""
        from backend.security import SessionManager
        
        manager = SessionManager(timeout_seconds=60)
        manager.start_session()
        
        assert manager.is_valid() is True
    
    
    def test_session_manager_detects_timeout(self):
        """Test that session manager detects timeout"""
        from backend.security import SessionManager
        import time
        
        manager = SessionManager(timeout_seconds=1)
        manager.start_session()
        
        # Wait for timeout
        time.sleep(1.1)
        
        assert manager.is_valid() is False
    
    
    def test_session_manager_refresh(self):
        """Test that session refresh extends session"""
        from backend.security import SessionManager
        import time
        
        manager = SessionManager(timeout_seconds=2)
        manager.start_session()
        
        # Wait 1 second
        time.sleep(1)
        
        # Refresh session
        manager.refresh()
        
        # Should still be valid
        assert manager.is_valid() is True
        
        # Wait another 1 second (total 2 from refresh)
        time.sleep(1)
        
        # Should still be valid
        assert manager.is_valid() is True


class TestSecurityValidator:
    """Test security validation"""
    
    def test_validate_order_valid_parameters(self):
        """Test validation of valid order parameters"""
        from backend.security import SecurityValidator
        
        result = SecurityValidator.validate_order_parameters(
            ticker='TTE',
            action='BUY',
            quantity=100,
            order_type='SMART'
        )
        
        assert result is True
    
    
    def test_validate_order_invalid_ticker(self):
        """Test validation rejects invalid ticker"""
        from backend.security import SecurityValidator
        
        with pytest.raises(ValueError):
            SecurityValidator.validate_order_parameters(
                ticker='',
                action='BUY',
                quantity=100,
                order_type='SMART'
            )
    
    
    def test_validate_order_invalid_action(self):
        """Test validation rejects invalid action"""
        from backend.security import SecurityValidator
        
        with pytest.raises(ValueError, match="Invalid action"):
            SecurityValidator.validate_order_parameters(
                ticker='TTE',
                action='INVALID',
                quantity=100,
                order_type='SMART'
            )
    
    
    def test_validate_order_invalid_quantity(self):
        """Test validation rejects invalid quantity"""
        from backend.security import SecurityValidator
        
        # Negative quantity
        with pytest.raises(ValueError, match="Invalid quantity"):
            SecurityValidator.validate_order_parameters(
                ticker='TTE',
                action='BUY',
                quantity=-10,
                order_type='SMART'
            )
        
        # Zero quantity
        with pytest.raises(ValueError, match="Invalid quantity"):
            SecurityValidator.validate_order_parameters(
                ticker='TTE',
                action='BUY',
                quantity=0,
                order_type='SMART'
            )
    
    
    def test_validate_order_invalid_order_type(self):
        """Test validation rejects invalid order type"""
        from backend.security import SecurityValidator
        
        with pytest.raises(ValueError, match="Invalid order type"):
            SecurityValidator.validate_order_parameters(
                ticker='TTE',
                action='BUY',
                quantity=100,
                order_type='INVALID'
            )
    
    
    def test_validate_data_quality_valid(self):
        """Test data quality validation on valid data"""
        from backend.security import SecurityValidator
        
        df = pd.DataFrame({
            'close': [50, 51, 52, 53, 54],
            'volume': [1000, 1100, 1200, 1300, 1400],
            'high': [51, 52, 53, 54, 55],
            'low': [49, 50, 51, 52, 53]
        })
        
        result = SecurityValidator.validate_data_quality(df)
        assert result == True  # Use == instead of is for numpy boolean compatibility
    
    
    def test_validate_data_missing_required_columns(self):
        """Test data validation rejects missing columns"""
        from backend.security import SecurityValidator
        
        df = pd.DataFrame({
            'open': [50, 51, 52],
            # Missing 'close' and 'volume'
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            SecurityValidator.validate_data_quality(df)
    
    
    def test_validate_data_invalid_highs_lows(self):
        """Test data validation rejects invalid high/low values"""
        from backend.security import SecurityValidator
        
        df = pd.DataFrame({
            'close': [50, 51, 52],
            'volume': [1000, 1100, 1200],
            'high': [49, 50, 51],  # Invalid: high < close
            'low': [51, 52, 53]    # Invalid: low > close
        })
        
        with pytest.raises(ValueError, match="Data integrity error"):
            SecurityValidator.validate_data_quality(df)
    
    
    def test_validate_data_quality_score(self):
        """Test data quality score calculation"""
        from backend.security import SecurityValidator
        
        # Data with no NaN values should pass
        df = pd.DataFrame({
            'close': [50, 51, 52, 53, 54],
            'volume': [1000, 1100, 1200, 1300, 1400],
        })
        
        # Add some valid but marginal data
        result = SecurityValidator.validate_data_quality(df)
        assert result is True or result >= 0.90


class TestStartupValidation:
    """Test startup security validation"""
    
    def test_validate_startup_with_valid_env(self):
        """Test startup validation passes with valid environment"""
        from backend.security import validate_startup
        
        with patch.dict(os.environ, {
            'IBKR_HOST': '127.0.0.1',
            'IBKR_PORT': '7497',
            'IBKR_CLIENT_ID': '1'
        }):
            result = validate_startup()
            assert result is True
    
    
    def test_validate_startup_fails_with_invalid_env(self):
        """Test startup validation fails with invalid environment"""
        from backend.security import validate_startup, _credential_manager
        
        # Reset singleton
        import backend.security
        backend.security._credential_manager = None
        
        with patch.dict(os.environ, {}, clear=True):
            result = validate_startup()
            # Should fail but not crash
            assert result is False

