"""
Job management service for data collection
"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
import subprocess
import platform
import time

from backend.models import SessionLocal, DataCollectionJob, JobStatus
from backend.config import logger


def retry_on_db_lock(func, max_retries=3, initial_wait=0.1):
    """
    Retry a function if it fails with database lock error
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_wait: Initial wait time in seconds
    
    Returns:
        Result of func()
    """
    import sqlite3
    from sqlalchemy.exc import OperationalError
    
    wait_time = initial_wait
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except (OperationalError, sqlite3.OperationalError) as e:
            if "database is locked" in str(e).lower():
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    wait_time *= 2  # Exponential backoff
                else:
                    logger.error(f"Database still locked after {max_retries} retries")
                    raise
            else:
                raise
    
    raise last_error


class JobManager:
    """Manage data collection jobs"""
    
    @staticmethod
    def create_job(
        ticker_symbol: str,
        ticker_name: str,
        source: str,
        duration: str = None,
        interval: str = None,
        created_by: str = None
    ) -> DataCollectionJob:
        """
        Create a new data collection job
        
        Args:
            ticker_symbol: Stock symbol
            ticker_name: Stock name
            source: Data source ('ibkr' or 'yahoo')
            duration: Duration/period for data collection
            interval: Data interval
            created_by: User who created the job
        
        Returns:
            Created job object
        """
        db = SessionLocal()
        try:
            # Generate temporary task ID (will be updated when Celery task starts)
            import uuid
            temp_task_id = f"temp-{uuid.uuid4()}"
            
            job = DataCollectionJob(
                celery_task_id=temp_task_id,
                ticker_symbol=ticker_symbol,
                ticker_name=ticker_name,
                source=source,
                duration=duration,
                interval=interval,
                status=JobStatus.PENDING,
                progress=0,
                created_by=created_by,
                created_at=datetime.utcnow()
            )
            
            db.add(job)
            
            # Retry on database lock
            def commit_job():
                """TODO: Add docstring."""
                db.commit()
                db.refresh(job)
            
            retry_on_db_lock(commit_job, max_retries=3)
            
            logger.info(f"Created job {job.id} for {ticker_symbol} from {source}")
            return job
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating job: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def update_job_task_id(job_id: int, celery_task_id: str) -> None:
        """Update job with actual Celery task ID"""
        db = SessionLocal()
        try:
            job = db.query(DataCollectionJob).filter(DataCollectionJob.id == job_id).first()
            if job:
                job.celery_task_id = celery_task_id
                # Retry on database lock
                def commit_update():
                    """TODO: Add docstring."""
                    db.commit()
                retry_on_db_lock(commit_update, max_retries=3)
        except Exception as e:
            logger.error(f"Error updating task ID: {e}")
            db.rollback()
        finally:
            db.close()
    
    @staticmethod
    def get_job(job_id: int) -> Optional[DataCollectionJob]:
        """Get job by ID"""
        db = SessionLocal()
        try:
            return db.query(DataCollectionJob).filter(DataCollectionJob.id == job_id).first()
        finally:
            db.close()
    
    @staticmethod
    def get_active_jobs() -> List[DataCollectionJob]:
        """Get all active (pending or running) jobs"""
        db = SessionLocal()
        try:
            return db.query(DataCollectionJob).filter(
                DataCollectionJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
            ).order_by(DataCollectionJob.created_at.desc()).all()
        finally:
            db.close()
    
    @staticmethod
    def get_recent_jobs(limit: int = 50) -> List[DataCollectionJob]:
        """Get recent jobs"""
        db = SessionLocal()
        try:
            return db.query(DataCollectionJob).order_by(
                DataCollectionJob.created_at.desc()
            ).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def get_jobs_by_status(status: JobStatus, limit: int = 50) -> List[DataCollectionJob]:
        """Get jobs by status"""
        db = SessionLocal()
        try:
            return db.query(DataCollectionJob).filter(
                DataCollectionJob.status == status
            ).order_by(DataCollectionJob.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def get_jobs_by_ticker(ticker_symbol: str, limit: int = 20) -> List[DataCollectionJob]:
        """Get jobs for a specific ticker"""
        db = SessionLocal()
        try:
            return db.query(DataCollectionJob).filter(
                DataCollectionJob.ticker_symbol == ticker_symbol
            ).order_by(DataCollectionJob.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def cancel_job(job_id: int) -> bool:
        """
        Cancel a pending or running job
        
        Returns:
            True if job was cancelled, False otherwise
        """
        db = SessionLocal()
        try:
            job = db.query(DataCollectionJob).filter(DataCollectionJob.id == job_id).first()
            
            if not job:
                logger.warning(f"Job {job_id} not found")
                return False
            
            if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
                logger.warning(f"Job {job_id} cannot be cancelled (status: {job.status.value})")
                return False  # Cannot cancel completed/failed jobs
            
            # Revoke Celery task if it exists
            if job.celery_task_id and not job.celery_task_id.startswith('temp-'):
                try:
                    from backend.celery_config import celery_app
                    # Revoke this specific task with terminate
                    celery_app.control.revoke(job.celery_task_id, terminate=True, signal='SIGKILL')
                    logger.info(f"Revoked Celery task {job.celery_task_id}")
                    
                    # Remove this specific task from queue if pending
                    # Note: purge() removes ALL tasks, so we just revoke the specific one
                    # The revoke with terminate=True should stop it from executing
                    
                except Exception as e:
                    logger.warning(f"Could not revoke Celery task: {e}")
                    
                # On Windows, try to kill and restart the worker to ensure clean state
                import platform
                if platform.system() == 'Windows':
                    try:
                        import subprocess
                        # Kill the worker
                        subprocess.run(['taskkill', '/F', '/IM', 'celery.exe'], 
                                     capture_output=True, timeout=5)
                        logger.info("Killed Celery worker process")
                        
                        # Purge the queue now that worker is stopped
                        try:
                            celery_app.control.purge()
                            logger.info("Purged Celery queue")
                        except Exception:
                            pass
                        
                        # Restart the worker
                        JobManager.restart_celery_worker()
                        
                    except Exception as e2:
                        logger.warning(f"Could not kill/restart worker: {e2}")
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.current_step = "Cancelled by user"
            job.completed_at = datetime.utcnow()
            job.progress = 0
            
            # Retry on database lock
            def commit_cancel():
                """TODO: Add docstring."""
                db.commit()
            retry_on_db_lock(commit_cancel, max_retries=3)
            
            logger.info(f"✅ Cancelled job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_statistics() -> Dict:
        """Get job statistics"""
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            stats = {
                'total': db.query(DataCollectionJob).count(),
                'pending': db.query(DataCollectionJob).filter(DataCollectionJob.status == JobStatus.PENDING).count(),
                'running': db.query(DataCollectionJob).filter(DataCollectionJob.status == JobStatus.RUNNING).count(),
                'completed': db.query(DataCollectionJob).filter(DataCollectionJob.status == JobStatus.COMPLETED).count(),
                'failed': db.query(DataCollectionJob).filter(DataCollectionJob.status == JobStatus.FAILED).count(),
                'cancelled': db.query(DataCollectionJob).filter(DataCollectionJob.status == JobStatus.CANCELLED).count(),
            }
            
            # Average completion time for completed jobs
            avg_time = db.query(
                func.avg(
                    func.strftime('%s', DataCollectionJob.completed_at) - 
                    func.strftime('%s', DataCollectionJob.started_at)
                )
            ).filter(DataCollectionJob.status == JobStatus.COMPLETED).scalar()
            
            stats['average_completion_time'] = int(avg_time) if avg_time else 0
            
            return stats
            
        finally:
            db.close()
    
    @staticmethod
    def restart_celery_worker() -> bool:
        """
        Restart Celery worker (Windows only)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if platform.system() != 'Windows':
                logger.warning("restart_celery_worker only supported on Windows")
                return False
            
            import os
            
            # Get project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Kill any existing celery processes
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'celery.exe'], 
                             capture_output=True, timeout=5)
                logger.info("Killed existing Celery processes")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not kill Celery processes: {e}")
            
            # Purge Redis queue
            try:
                subprocess.run(
                    ['celery', '-A', 'backend.celery_config', 'purge', '-f'],
                    cwd=project_root,
                    capture_output=True,
                    timeout=10
                )
                logger.info("Purged Celery queue")
            except Exception as e:
                logger.warning(f"Could not purge queue: {e}")
            
            # Build command to start Celery worker
            # Use absolute path to avoid issues
            activate_script = os.path.join(project_root, 'venv', 'Scripts', 'activate.bat')
            
            # Create command that activates venv and starts celery
            cmd = f'start "Celery Worker - Boursicotor" cmd /k "cd /d {project_root} && call {activate_script} && celery -A backend.celery_config worker --loglevel=info --pool=solo"'
            
            # Execute command
            subprocess.Popen(cmd, shell=True)
            
            logger.info("✅ Celery worker restart command sent")
            time.sleep(3)  # Give it time to start
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart Celery worker: {e}")
            return False
