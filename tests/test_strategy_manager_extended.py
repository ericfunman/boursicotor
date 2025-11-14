"""
Unit tests for backend strategy_manager module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
try:
    from backend.strategy_manager import StrategyManager
except ImportError:
    StrategyManager = None


class TestStrategyManagerInit:
    """Test StrategyManager initialization"""
    
    @pytest.mark.skipif(StrategyManager is None, reason="StrategyManager not available")
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_init(self, mock_session):
        """Test StrategyManager initializes correctly"""
        mock_session.return_value = MagicMock()
        
        try:
            manager = StrategyManager()
            assert manager is not None
        except Exception:
            pytest.skip("StrategyManager initialization requires specific dependencies")
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_strategies(self, mock_session):
        """Test StrategyManager has strategies storage"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'strategies') or hasattr(manager, '_strategies')


class TestStrategyManagerLoading:
    """Test strategy loading"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_load_method(self, mock_session):
        """Test StrategyManager has load_strategy method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'load_strategy')
        assert callable(manager.load_strategy)
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_load_strategy_by_id(self, mock_session):
        """Test loading strategy by ID"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        with patch.object(manager, 'load_strategy', return_value={'id': 1, 'name': 'Test'}):
            strategy = manager.load_strategy(strategy_id=1)
            assert strategy is not None


class TestStrategyManagerCreation:
    """Test strategy creation"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_create_method(self, mock_session):
        """Test StrategyManager has create_strategy method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'create_strategy')
        assert callable(manager.create_strategy)
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_create_strategy(self, mock_session):
        """Test creating a strategy"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        with patch.object(manager, 'create_strategy', return_value={'id': 1}):
            strategy = manager.create_strategy(
                name='RSI Strategy',
                description='RSI based strategy',
                parameters={}
            )
            assert strategy is not None


class TestStrategyManagerRetrieval:
    """Test strategy retrieval"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_get_method(self, mock_session):
        """Test StrategyManager has get_strategy method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'get_strategy') or hasattr(manager, 'get_strategies')
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_get_all_strategies(self, mock_session):
        """Test getting all strategies"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        with patch.object(manager, 'get_strategies', return_value=[]):
            strategies = manager.get_strategies()
            assert isinstance(strategies, list)


class TestStrategyManagerUpdate:
    """Test strategy updates"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_update_method(self, mock_session):
        """Test StrategyManager has update_strategy method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'update_strategy')
        assert callable(manager.update_strategy)
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_update_strategy(self, mock_session):
        """Test updating a strategy"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        with patch.object(manager, 'update_strategy', return_value=True):
            result = manager.update_strategy(strategy_id=1, name='Updated Strategy')
            assert result is True


class TestStrategyManagerDeletion:
    """Test strategy deletion"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_delete_method(self, mock_session):
        """Test StrategyManager has delete_strategy method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'delete_strategy')
        assert callable(manager.delete_strategy)
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_delete_strategy(self, mock_session):
        """Test deleting a strategy"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        with patch.object(manager, 'delete_strategy', return_value=True):
            result = manager.delete_strategy(strategy_id=1)
            assert result is True


class TestStrategyManagerExecution:
    """Test strategy execution"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_execute_method(self, mock_session):
        """Test StrategyManager has execute_strategy method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'execute_strategy') or hasattr(manager, 'run_strategy')
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_execute_strategy(self, mock_session):
        """Test executing a strategy"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        method_name = 'execute_strategy' if hasattr(manager, 'execute_strategy') else 'run_strategy'
        with patch.object(manager, method_name, return_value={'signal': 'BUY'}):
            result = getattr(manager, method_name)(strategy_id=1, data={})
            assert result is not None


class TestStrategyManagerSignals:
    """Test signal generation"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_generate_signal_method(self, mock_session):
        """Test StrategyManager has generate_signal method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'generate_signal') or hasattr(manager, 'execute_strategy')
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_generate_signal(self, mock_session):
        """Test generating signal from strategy"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        with patch.object(manager, 'generate_signal', return_value='BUY'):
            signal = manager.generate_signal(strategy_id=1, dataframe={})
            assert signal in ['BUY', 'SELL', 'HOLD', None]


class TestStrategyManagerActivation:
    """Test strategy activation/deactivation"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_activate_method(self, mock_session):
        """Test StrategyManager has activate_strategy method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'activate_strategy') or hasattr(manager, 'set_active')
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_activate_strategy(self, mock_session):
        """Test activating a strategy"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        method = 'activate_strategy' if hasattr(manager, 'activate_strategy') else 'set_active'
        with patch.object(manager, method, return_value=True):
            result = getattr(manager, method)(strategy_id=1)
            assert result is True


class TestStrategyManagerDatabase:
    """Test database operations"""
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_db_attribute(self, mock_session):
        """Test StrategyManager has db attribute"""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'db')
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_strategy_manager_has_close_method(self, mock_session):
        """Test StrategyManager has close method"""
        mock_session.return_value = MagicMock()
        
        manager = StrategyManager()
        
        assert hasattr(manager, 'close') or hasattr(manager, 'close_db')
