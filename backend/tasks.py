"""
Celery tasks for asynchronous data collection
"""
from celery import Task
from datetime import datetime
from backend.celery_config import celery_app
from backend.models import SessionLocal, DataCollectionJob, JobStatus
from backend.config import logger


class DatabaseTask(Task):
    """Base task with database session management"""
    _db = None
    
    @property
    def db(self):
        """TODO: Add docstring."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """TODO: Add docstring."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask)
def collect_data_ibkr(
    self,
    job_id: int,
    ticker_symbol: str,
    ticker_name: str,
    duration: str,
    bar_size: str,
    interval_db: str
):
    """
    Collect historical data from IBKR
    
    Args:
        job_id: Database job ID
        ticker_symbol: Stock symbol
        ticker_name: Stock name
        duration: IBKR duration string (e.g., '1 M')
        bar_size: IBKR bar size (e.g., '5 secs')
        interval_db: Database interval format (e.g., '5sec')
    """
    db = self.db
    job = db.query(DataCollectionJob).filter(DataCollectionJob.id == job_id).first()
    
    if not job:
        logger.error(f"Job {job_id} not found")
        return {'success': False, 'error': 'Job not found'}
    
    try:
        # Update job status to running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.current_step = "Initializing IBKR connection..."
        db.commit()
        
        # Import here to avoid circular imports
        from backend.ibkr_collector import IBKRCollector
        import random
        
        # Use a dynamic client_id for Celery tasks (4-999)
        # This avoids conflicts with UI (client_id=1) and allows multiple concurrent Celery workers
        # Each task disconnects after completion, freeing the client_id for reuse
        celery_client_id = random.randint(4, 999)
        logger.info(f"Celery task using client_id={celery_client_id}")
        
        collector = IBKRCollector(client_id=celery_client_id)
        
        # Connect to IBKR
        job.current_step = "Connecting to IBKR..."
        job.progress = 5
        db.commit()
        
        if not collector.connect():
            raise Exception("Failed to connect to IBKR")
        
        # Progress callback to update job progress
        def progress_callback(current, total):
            """Update job progress in database"""
            try:
                # Update progress (5% for connection, 90% for data collection, 5% for saving)
                progress = 5 + int((current / total) * 85)
                job.progress = min(progress, 90)
                job.current_step = f"Collecting data chunk {current}/{total}..."
                db.commit()
                
                # Update Celery task state for Flower monitoring
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': current,
                        'total': total,
                        'progress': job.progress,
                        'status': job.current_step
                    }
                )
            except Exception as e:
                logger.error(f"Error updating progress: {e}")
        
        # Collect data
        job.current_step = f"Collecting {ticker_symbol} data from IBKR..."
        job.progress = 10
        db.commit()
        
        logger.info(f"🚀 Starting data collection for job {job_id}: {ticker_symbol}")
        
        # Use streaming mode for better memory efficiency
        result = collector.collect_and_save_streaming(
            symbol=ticker_symbol,
            duration=duration,
            bar_size=bar_size,
            interval=interval_db,
            name=ticker_name,
            progress_callback=progress_callback
        )
        
        logger.info(f"📊 Collection result for job {job_id}: success={result.get('success')}, total_records={result.get('total_records')}, error={result.get('error')}")
        
        # Update job with results
        job.progress = 95
        job.current_step = "Finalizing..."
        db.commit()
        
        if result['success']:
            job.status = JobStatus.COMPLETED
            job.records_new = result.get('new_records', 0)
            job.records_updated = result.get('updated_records', 0)
            job.records_total = result.get('total_records', 0)
            job.progress = 100
            job.current_step = "Completed successfully!"
            job.completed_at = datetime.utcnow()
            logger.info(f"✅ Job {job_id} completed: {job.records_new} new, {job.records_updated} updated, total: {job.records_total}")
        else:
            job.status = JobStatus.FAILED
            job.error_message = result.get('error', 'Unknown error')
            job.progress = 0
            job.current_step = "Failed"
            job.completed_at = datetime.utcnow()
            logger.error(f"❌ Job {job_id} failed: {job.error_message}")
        
        db.commit()
        return result
        
    except Exception as e:
        # Update job as failed
        logger.error(f"Error in collect_data_ibkr job {job_id}: {e}", exc_info=True)
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.progress = 0
        job.current_step = "Failed with exception"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # Re-raise for Celery to handle
        raise
    
    finally:
        # Always disconnect from IBKR to avoid connection leaks
        try:
            if collector and collector.connected:
                collector.disconnect()
                logger.info(f"🔌 Disconnected from IBKR for job {job_id}")
        except Exception as disconnect_error:
            logger.warning(f"Error disconnecting IBKR for job {job_id}: {disconnect_error}")


@celery_app.task
def cleanup_old_jobs(days_to_keep: int = 7):
    """
    Cleanup completed jobs older than specified days
    
    Args:
        days_to_keep: Number of days to keep completed jobs
    """
    db = SessionLocal()
    try:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted = db.query(DataCollectionJob).filter(
            DataCollectionJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
            DataCollectionJob.completed_at < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted} old jobs")
        return {'deleted': deleted}
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {e}")
        db.rollback()
        raise
    finally:
        db.close()
