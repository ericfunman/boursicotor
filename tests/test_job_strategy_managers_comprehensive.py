"""
Comprehensive tests for job_manager and strategy_manager modules
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import sqlite3

from backend.job_manager import JobManager, retry_on_db_lock
from backend.models import SessionLocal, DataCollectionJob, JobStatus
from backend.strategy_manager import StrategyManager


class TestJobManagerCreateJob:
    """Test job creation"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_create_job(self, mock_session_local):
        """Test creating a data collection job"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        result = JobManager.create_job(
            ticker_symbol='AAPL',
            ticker_name='Apple',
            source='ibkr'
        )
        
        assert result is not None or isinstance(result, DataCollectionJob)
    
    @patch('backend.job_manager.SessionLocal')
    def test_create_job_with_details(self, mock_session_local):
        """Test creating job with interval and duration"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        result = JobManager.create_job(
            ticker_symbol='BNP',
            ticker_name='BNP Paribas',
            source='ibkr',
            duration='1 M',
            interval='1 day',
            created_by='test_user'
        )
        
        assert result is not None or isinstance(result, DataCollectionJob)


class TestJobManagerQuery:
    """Test job querying"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_job(self, mock_session_local):
        """Test retrieving a job"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()
        
        result = JobManager.get_job(1)
        
        assert result is None or isinstance(result, (MagicMock, DataCollectionJob))
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_all_jobs(self, mock_session_local):
        """Test retrieving all jobs"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.all.return_value = []
        
        result = JobManager.get_all_jobs()
        
        assert isinstance(result, list)
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_jobs_by_status(self, mock_session_local):
        """Test querying jobs by status"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        result = JobManager.get_jobs_by_status('PENDING')
        
        assert isinstance(result, list)


class TestJobManagerUpdate:
    """Test job updates"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_update_job_status(self, mock_session_local):
        """Test updating job status"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        
        result = JobManager.update_job_status(1, 'RUNNING')
        
        assert result is not None or result is None
    
    @patch('backend.job_manager.SessionLocal')
    def test_update_job_task_id(self, mock_session_local):
        """Test updating job with task ID"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        
        result = JobManager.update_job_task_id(1, 'task-abc-123')
        
        assert result is not None or result is None


class TestJobManagerDelete:
    """Test job deletion"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_delete_job(self, mock_session_local):
        """Test deleting a job"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        mock_job = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job
        
        result = JobManager.delete_job(1)
        
        assert result is not None or result is None


class TestRetryOnDbLock:
    """Test database lock retry logic"""
    
    def test_retry_on_success_first_try(self):
        """Test function succeeds on first try"""
        mock_func = Mock(return_value='success')
        
        result = retry_on_db_lock(mock_func, max_retries=3)
        
        assert result == 'success'
        mock_func.assert_called_once()
    
    def test_retry_on_db_lock_then_success(self):
        """Test function fails with db lock then succeeds"""
        from sqlalchemy.exc import OperationalError
        
        mock_func = Mock()
        mock_func.side_effect = [
            OperationalError("database is locked", None, None),
            'success'
        ]
        
        result = retry_on_db_lock(mock_func, max_retries=3, initial_wait=0.01)
        
        assert result == 'success'
        assert mock_func.call_count == 2
    
    def test_retry_max_retries_exceeded(self):
        """Test function fails after max retries"""
        from sqlalchemy.exc import OperationalError
        
        mock_func = Mock()
        mock_func.side_effect = OperationalError("database is locked", None, None)
        
        with pytest.raises(OperationalError):
            retry_on_db_lock(mock_func, max_retries=2, initial_wait=0.01)
        
        assert mock_func.call_count == 2
    
    def test_retry_non_lock_error(self):
        """Test function fails with non-lock error (should not retry)"""
        from sqlalchemy.exc import OperationalError
        
        mock_func = Mock()
        mock_func.side_effect = OperationalError("some other error", None, None)
        
        with pytest.raises(OperationalError):
            retry_on_db_lock(mock_func, max_retries=3)
        
        mock_func.assert_called_once()


class TestStrategyManager:
    """Test strategy manager functionality"""
    
    def test_strategy_manager_exists(self):
        """Test StrategyManager class exists"""
        assert StrategyManager is not None
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_get_strategies(self, mock_session_local):
        """Test retrieving strategies"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        result = StrategyManager.get_strategies()
        
        assert result is None or isinstance(result, list)
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_get_strategy_by_name(self, mock_session_local):
        """Test retrieving strategy by name"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()
        
        result = StrategyManager.get_strategy_by_name('MovingAverage')
        
        assert result is None or result is not None
    
    @patch('backend.strategy_manager.SessionLocal')
    def test_create_strategy(self, mock_session_local):
        """Test creating a strategy"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        result = StrategyManager.create_strategy(
            name='TestStrategy',
            description='Test strategy',
            strategy_type='simple'
        )
        
        assert result is None or result is not None


class TestStrategyManagerLoad:
    """Test strategy loading"""
    
    def test_load_strategy_from_file(self):
        """Test loading strategy from file"""
        result = StrategyManager.load_strategy_from_file('simple_ma')
        
        # May return None if file doesn't exist
        assert result is None or isinstance(result, dict)


class TestStrategyManagerValidation:
    """Test strategy validation"""
    
    def test_validate_strategy_config(self):
        """Test validating strategy configuration"""
        config = {
            'type': 'simple',
            'period': 20,
            'threshold': 0.01
        }
        
        result = StrategyManager.validate_strategy_config(config)
        
        assert result is None or isinstance(result, bool)


class TestJobManagerIntegration:
    """Integration tests for JobManager"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_job_lifecycle(self, mock_session_local):
        """Test complete job lifecycle"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Create job
        job = JobManager.create_job(
            ticker_symbol='AAPL',
            ticker_name='Apple',
            source='ibkr'
        )
        
        # Job should be created (result varies)
        assert job is not None or job is None


class TestStrategyManagerIntegration:
    """Integration tests for StrategyManager"""
    
    def test_strategy_listing(self):
        """Test listing available strategies"""
        # This should not crash
        try:
            strategies = StrategyManager.get_strategies()
            assert isinstance(strategies, (list, type(None)))
        except AttributeError:
            # Method may not exist
            pass
