"""
Job management service for data collection
"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import SessionLocal, DataCollectionJob, JobStatus
from backend.config import logger


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
            db.commit()
            db.refresh(job)
            
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
                db.commit()
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
                return False
            
            if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
                return False  # Cannot cancel completed/failed jobs
            
            # Revoke Celery task if it exists
            if job.celery_task_id and not job.celery_task_id.startswith('temp-'):
                from backend.celery_config import celery_app
                celery_app.control.revoke(job.celery_task_id, terminate=True)
            
            # Update job status
            job.status = JobStatus.CANCELLED
            job.current_step = "Cancelled by user"
            job.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Cancelled job {job_id}")
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
                'pending': db.query(DataCollectionJob).filter(JobStatus.PENDING).count(),
                'running': db.query(DataCollectionJob).filter(JobStatus.RUNNING).count(),
                'completed': db.query(DataCollectionJob).filter(JobStatus.COMPLETED).count(),
                'failed': db.query(DataCollectionJob).filter(JobStatus.FAILED).count(),
                'cancelled': db.query(DataCollectionJob).filter(JobStatus.CANCELLED).count(),
            }
            
            # Average completion time for completed jobs
            avg_time = db.query(
                func.avg(
                    func.strftime('%s', DataCollectionJob.completed_at) - 
                    func.strftime('%s', DataCollectionJob.started_at)
                )
            ).filter(DataCollectionJob.status == JobStatus.COMPLETED).scalar()
            
            stats['avg_completion_time_seconds'] = int(avg_time) if avg_time else 0
            
            return stats
            
        finally:
            db.close()
