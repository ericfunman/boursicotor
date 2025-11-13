"""
Focused tests for security.py - Target: 50%+ coverage
Focus on CredentialManager and basic security operations
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestSecurityImport:
    """Test security module import"""
    
    def test_security_module_imports(self):
        """Test security module can be imported"""
        from backend.security import CredentialManager
        assert CredentialManager is not None
    
    def test_credential_manager_class_exists(self):
        """Test CredentialManager class is defined"""
        from backend.security import CredentialManager
        assert hasattr(CredentialManager, '__init__')
        assert hasattr(CredentialManager, 'get_credential')


class TestCredentialManagerConstants:
    """Test CredentialManager constants"""
    
    def test_rate_limit_constant(self):
        """Test IBKR rate limit constant"""
        from backend.security import CredentialManager
        assert CredentialManager.IBKR_RATE_LIMIT == 100
    
    def test_rate_window_constant(self):
        """Test rate window constant"""
        from backend.security import CredentialManager
        assert CredentialManager.IBKR_RATE_WINDOW == 60
    
    def test_session_timeout_constant(self):
        """Test session timeout constant"""
        from backend.security import CredentialManager
        assert CredentialManager.SESSION_TIMEOUT == 30 * 60
    
    def test_max_retries_constant(self):
        """Test max retries constant"""
        from backend.security import CredentialManager
        assert CredentialManager.MAX_RETRIES == 3


class TestCredentialManagerInitialization:
    """Test CredentialManager initialization"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_credential_manager_can_be_instantiated(self):
        """Test creating CredentialManager with valid credentials"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        assert manager is not None
        assert manager.credentials is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_credential_manager_fails_without_credentials(self):
        """Test CredentialManager raises error without env vars"""
        from backend.security import CredentialManager
        
        with pytest.raises(ValueError):
            CredentialManager()
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_credential_manager_stores_credentials(self):
        """Test CredentialManager stores credentials"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        assert 'IBKR_HOST' in manager.credentials
        assert manager.credentials['IBKR_HOST'] == 'localhost'


class TestGetCredentialMethod:
    """Test get_credential static method"""
    
    @patch.dict(os.environ, {'TEST_KEY': 'test_value'})
    def test_get_credential_returns_value(self):
        """Test get_credential returns environment variable"""
        from backend.security import CredentialManager
        value = CredentialManager.get_credential('TEST_KEY')
        assert value == 'test_value'
    
    def test_get_credential_with_default(self):
        """Test get_credential returns default when key missing"""
        from backend.security import CredentialManager
        value = CredentialManager.get_credential('NONEXISTENT_KEY', 'default_value')
        assert value == 'default_value'
    
    def test_get_credential_returns_none_by_default(self):
        """Test get_credential returns None when key missing and no default"""
        from backend.security import CredentialManager
        value = CredentialManager.get_credential('NONEXISTENT_KEY')
        assert value is None


class TestGetIBKRConfig:
    """Test get_ibkr_config method"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_get_ibkr_config_returns_dict(self):
        """Test get_ibkr_config returns dictionary"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        config = manager.get_ibkr_config()
        
        assert isinstance(config, dict)
        assert 'host' in config
        assert 'port' in config
        assert 'client_id' in config
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_get_ibkr_config_values(self):
        """Test get_ibkr_config returns correct values"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        config = manager.get_ibkr_config()
        
        assert config['host'] == 'localhost'
        assert config['port'] == 7497
        assert config['client_id'] == 1
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'remote.broker.com',
        'IBKR_PORT': '7498',
        'IBKR_CLIENT_ID': '10'
    })
    def test_get_ibkr_config_custom_values(self):
        """Test get_ibkr_config with custom values"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        config = manager.get_ibkr_config()
        
        assert config['host'] == 'remote.broker.com'
        assert config['port'] == 7498
        assert config['client_id'] == 10


class TestCredentialValidation:
    """Test credential validation"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_validate_credentials_success(self):
        """Test _validate_credentials succeeds with all required vars"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        # If we got here, validation passed
        pass  # S5914: assert always true
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        # Missing IBKR_PORT and IBKR_CLIENT_ID
    }, clear=True)
    def test_validate_credentials_missing_host(self):
        """Test _validate_credentials fails when missing host"""
        from backend.security import CredentialManager
        
        with pytest.raises(ValueError) as exc_info:
            CredentialManager()
        
        assert 'Missing required environment variables' in str(exc_info.value)


class TestSecurityModuleFunctions:
    """Test other security module functions"""
    
    def test_security_module_has_logger(self):
        """Test security module has logger"""
        import backend.security
        assert hasattr(backend.security, 'logger')
    
    def test_security_module_content(self):
        """Test security module has expected content"""
        import backend.security
        
        content = dir(backend.security)
        assert 'CredentialManager' in content


class TestCredentialManagerAttributes:
    """Test CredentialManager attributes"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_credential_manager_has_credentials_dict(self):
        """Test CredentialManager has credentials dictionary"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        assert hasattr(manager, 'credentials')
        assert isinstance(manager.credentials, dict)
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_credentials_dict_is_populated(self):
        """Test credentials dict is populated after init"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        assert len(manager.credentials) > 0


class TestSecurityIntegration:
    """Integration tests for security module"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_credential_manager_lifecycle(self):
        """Test CredentialManager complete lifecycle"""
        from backend.security import CredentialManager
        
        # Create
        manager = CredentialManager()
        assert manager is not None
        
        # Get config
        config = manager.get_ibkr_config()
        assert config is not None
        
        # Get credential
        value = CredentialManager.get_credential('IBKR_HOST')
        assert value is not None


class TestSecurityErrorHandling:
    """Test error handling in security module"""
    
    def test_get_credential_safe_with_nonexistent_key(self):
        """Test get_credential doesn't crash on missing key"""
        from backend.security import CredentialManager
        
        # Should not raise, just return None or default
        result = CredentialManager.get_credential('DEFINITELY_NONEXISTENT_KEY_12345')
        assert result is None
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_credential_manager_multiple_instances(self):
        """Test multiple CredentialManager instances can be created"""
        from backend.security import CredentialManager
        
        manager1 = CredentialManager()
        manager2 = CredentialManager()
        
        assert manager1 is not None
        assert manager2 is not None
        assert manager1.credentials == manager2.credentials


class TestEnvironmentVariableHandling:
    """Test environment variable handling"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1',
        'EXTRA_VAR': 'extra_value'
    })
    def test_extra_env_vars_not_required(self):
        """Test CredentialManager ignores extra env vars"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        assert manager is not None
    
    def test_invalid_port_error_handling(self):
        """Test invalid port causes appropriate error"""
        from backend.security import CredentialManager
        
        with patch.dict(os.environ, {
            'IBKR_HOST': 'localhost',
            'IBKR_PORT': 'invalid_port',
            'IBKR_CLIENT_ID': '1'
        }):
            manager = CredentialManager()
            # get_ibkr_config will try to convert, should handle gracefully
            with pytest.raises(ValueError):
                manager.get_ibkr_config()


class TestCredentialManagerPortHandling:
    """Test port number handling"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '1'
    })
    def test_valid_port_conversion(self):
        """Test valid port converts correctly"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        config = manager.get_ibkr_config()
        
        # Should convert string port to int
        assert config['port'] == 7497
        assert isinstance(config['port'], int)


class TestCredentialManagerClientIDHandling:
    """Test client ID handling"""
    
    @patch.dict(os.environ, {
        'IBKR_HOST': 'localhost',
        'IBKR_PORT': '7497',
        'IBKR_CLIENT_ID': '10'
    })
    def test_client_id_conversion(self):
        """Test client ID converts correctly"""
        from backend.security import CredentialManager
        manager = CredentialManager()
        config = manager.get_ibkr_config()
        
        # Should convert string client ID to int
        assert config['client_id'] == 10
        assert isinstance(config['client_id'], int)
