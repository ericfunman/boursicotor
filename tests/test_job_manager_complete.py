"""
Complete tests for job_manager.py - Target: 70%+ coverage
Focus: Job creation, querying, status management, error handling
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
import sqlite3

from backend.job_manager import JobManager, retry_on_db_lock
from backend.models import DataCollectionJob, JobStatus


class TestRetryOnDbLock:
    """Test retry_on_db_lock decorator/wrapper"""
    
    def test_retry_on_db_lock_success_first_time(self):
        """Test retry succeeds on first attempt"""
        result = retry_on_db_lock(lambda: "success", max_retries=3)
        assert result == "success"
    
    def test_retry_on_db_lock_success_after_retry(self):
        """Test retry succeeds after retry"""
        call_count = 0
        
        def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OperationalError("database is locked", None, None)
            return "success"
        
        result = retry_on_db_lock(mock_func, max_retries=3, initial_wait=0.001)
        assert result == "success"
        assert call_count == 2
    
    def test_retry_on_db_lock_fails_after_max_retries(self):
        """Test retry fails after max retries"""
        def mock_func():
            raise OperationalError("database is locked", None, None)
        
        with pytest.raises(OperationalError):
            retry_on_db_lock(mock_func, max_retries=2, initial_wait=0.001)
    
    def test_retry_on_db_lock_non_lock_error_immediate(self):
        """Test non-lock errors raise immediately"""
        def mock_func():
            raise OperationalError("other error", None, None)
        
        with pytest.raises(OperationalError):
            retry_on_db_lock(mock_func, max_retries=3)
    
    def test_retry_on_db_lock_sqlite_lock_error(self):
        """Test sqlite3 lock error is retried"""
        call_count = 0
        
        def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise sqlite3.OperationalError("database is locked")
            return "success"
        
        result = retry_on_db_lock(mock_func, max_retries=3, initial_wait=0.001)
        assert result == "success"


class TestJobManagerCreateJob:
    """Test JobManager.create_job method"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_create_job_basic(self, mock_session_local):
        """Test creating a basic job"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        job = JobManager.create_job(
            ticker_symbol="AAPL",
            ticker_name="Apple Inc.",
            source="ibkr",
            duration="1y",
            interval="1day"
        )
        
        assert job is not None
        assert job.ticker_symbol == "AAPL"
        assert job.source == "ibkr"
        assert job.status == JobStatus.PENDING
        assert job.progress == 0
        mock_db.close.assert_called()
    
    @patch('backend.job_manager.SessionLocal')
    def test_create_job_with_user(self, mock_session_local):
        """Test creating a job with user info"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        job = JobManager.create_job(
            ticker_symbol="MSFT",
            ticker_name="Microsoft",
            source="ibkr",
            created_by="user@example.com"
        )
        
        assert job.created_by == "user@example.com"
        assert job.created_at is not None
    
    @patch('backend.job_manager.SessionLocal')
    def test_create_job_generates_task_id(self, mock_session_local):
        """Test job has temp task ID"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        job = JobManager.create_job(
            ticker_symbol="GOOG",
            ticker_name="Google",
            source="ibkr"
        )
        
        assert job.celery_task_id is not None
        assert job.celery_task_id.startswith("temp-")


class TestJobManagerGetJob:
    """Test JobManager.get_job method"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_job_exists(self, mock_session_local):
        """Test retrieving existing job"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_job = MagicMock(spec=DataCollectionJob)
        mock_job.id = 1
        mock_job.ticker_symbol = "AAPL"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        job = JobManager.get_job(job_id=1)
        
        assert job is not None
        assert job.ticker_symbol == "AAPL"
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_job_not_exists(self, mock_session_local):
        """Test retrieving non-existent job"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        job = JobManager.get_job(job_id=999)
        
        assert job is None


class TestJobManagerGetJobs:
    """Test JobManager.get_jobs method"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_jobs_all(self, mock_session_local):
        """Test retrieving all jobs"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_jobs = [
            MagicMock(id=1, ticker_symbol="AAPL"),
            MagicMock(id=2, ticker_symbol="MSFT")
        ]
        mock_db.query.return_value.all.return_value = mock_jobs
        
        jobs = JobManager.get_jobs()
        
        assert len(jobs) == 2
        assert jobs[0].ticker_symbol == "AAPL"
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_jobs_by_status(self, mock_session_local):
        """Test retrieving jobs by status"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_jobs = [MagicMock(status=JobStatus.COMPLETED)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_jobs
        
        jobs = JobManager.get_jobs(status=JobStatus.COMPLETED)
        
        assert len(jobs) == 1


class TestJobManagerUpdateJob:
    """Test JobManager.update_job method"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_update_job_status(self, mock_session_local):
        """Test updating job status"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_job = MagicMock(spec=DataCollectionJob)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        updated = JobManager.update_job(
            job_id=1,
            status=JobStatus.RUNNING
        )
        
        assert updated is not None
        assert mock_job.status == JobStatus.RUNNING
    
    @patch('backend.job_manager.SessionLocal')
    def test_update_job_progress(self, mock_session_local):
        """Test updating job progress"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_job = MagicMock(spec=DataCollectionJob)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        updated = JobManager.update_job(
            job_id=1,
            progress=50
        )
        
        assert mock_job.progress == 50
    
    @patch('backend.job_manager.SessionLocal')
    def test_update_job_not_exists(self, mock_session_local):
        """Test updating non-existent job"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        updated = JobManager.update_job(job_id=999)
        
        assert updated is None


class TestJobManagerDeleteJob:
    """Test JobManager.delete_job method"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_delete_job_exists(self, mock_session_local):
        """Test deleting existing job"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_job = MagicMock(spec=DataCollectionJob)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        result = JobManager.delete_job(job_id=1)
        
        assert result is True
        mock_db.delete.assert_called_with(mock_job)
    
    @patch('backend.job_manager.SessionLocal')
    def test_delete_job_not_exists(self, mock_session_local):
        """Test deleting non-existent job"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = JobManager.delete_job(job_id=999)
        
        assert result is False


class TestJobManagerJobStatus:
    """Test job status transitions"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_job_status_workflow(self, mock_session_local):
        """Test typical job status workflow"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Create job - starts as PENDING
        job = JobManager.create_job(
            ticker_symbol="TSLA",
            ticker_name="Tesla",
            source="ibkr"
        )
        assert job.status == JobStatus.PENDING
        
        # Update to RUNNING
        mock_db.query.return_value.filter.return_value.first.return_value = job
        JobManager.update_job(job_id=job.id, status=JobStatus.RUNNING)
        assert job.status == JobStatus.RUNNING
        
        # Update to COMPLETED
        JobManager.update_job(job_id=job.id, status=JobStatus.COMPLETED)
        assert job.status == JobStatus.COMPLETED


class TestJobManagerErrorHandling:
    """Test error handling in JobManager"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_create_job_database_error(self, mock_session_local):
        """Test handling database error during job creation"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.add.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            JobManager.create_job(
                ticker_symbol="BAD",
                ticker_name="Bad Corp",
                source="ibkr"
            )
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_job_database_error(self, mock_session_local):
        """Test handling database error during job retrieval"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            JobManager.get_job(job_id=1)


class TestJobManagerEdgeCases:
    """Test edge cases"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_create_job_minimal_params(self, mock_session_local):
        """Test creating job with minimal parameters"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        job = JobManager.create_job(
            ticker_symbol="XYZ",
            ticker_name="XYZ Corp",
            source="ibkr"
        )
        
        assert job is not None
        assert job.duration is None
        assert job.interval is None
    
    @patch('backend.job_manager.SessionLocal')
    def test_get_jobs_empty_list(self, mock_session_local):
        """Test retrieving jobs when none exist"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.all.return_value = []
        
        jobs = JobManager.get_jobs()
        
        assert jobs == []
    
    @patch('backend.job_manager.SessionLocal')
    def test_update_job_multiple_fields(self, mock_session_local):
        """Test updating multiple job fields at once"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        mock_job = MagicMock(spec=DataCollectionJob)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        JobManager.update_job(
            job_id=1,
            status=JobStatus.RUNNING,
            progress=75,
            celery_task_id="task-123"
        )
        
        assert mock_job.status == JobStatus.RUNNING
        assert mock_job.progress == 75
        assert mock_job.celery_task_id == "task-123"


class TestJobManagerIntegration:
    """Integration-like tests with full workflow"""
    
    @patch('backend.job_manager.SessionLocal')
    def test_complete_job_lifecycle(self, mock_session_local):
        """Test complete job lifecycle"""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # Create
        job = JobManager.create_job(
            ticker_symbol="NVDA",
            ticker_name="NVIDIA",
            source="ibkr",
            duration="1y",
            interval="1day",
            created_by="test_user"
        )
        
        assert job.status == JobStatus.PENDING
        assert job.progress == 0
        
        # Retrieve
        mock_db.query.return_value.filter.return_value.first.return_value = job
        retrieved = JobManager.get_job(job_id=job.id)
        assert retrieved is not None
        
        # Update to running
        JobManager.update_job(
            job_id=job.id,
            status=JobStatus.RUNNING,
            celery_task_id="celery-task-123"
        )
        assert job.status == JobStatus.RUNNING
        
        # Update progress
        JobManager.update_job(job_id=job.id, progress=100)
        assert job.progress == 100
        
        # Complete
        JobManager.update_job(
            job_id=job.id,
            status=JobStatus.COMPLETED
        )
        assert job.status == JobStatus.COMPLETED
