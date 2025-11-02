#!/usr/bin/env python3
"""
Test cancel job functionality
"""
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.job_manager import JobManager
from backend.models import SessionLocal, DataCollectionJob, JobStatus

# Create test job
db = SessionLocal()
try:
    job = DataCollectionJob(
        celery_task_id='test-cancel-123',
        ticker_symbol='TEST',
        ticker_name='Test',
        source='IBKR',
        duration='1 M',
        interval='1min',
        status=JobStatus.RUNNING,
        created_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    job_id = job.id
    print(f"Created test job {job_id}")
finally:
    db.close()

# Test cancel
print("Testing JobManager.cancel_job()...")
success = JobManager.cancel_job(job_id)
print(f"Cancel result: {success}")

# Verify status
db = SessionLocal()
try:
    test_job = db.query(DataCollectionJob).filter(DataCollectionJob.id == job_id).first()
    if test_job:
        print(f"Job status after cancel: {test_job.status.value}")
        print(f"Job step: {test_job.current_step}")
        
        # Cleanup
        db.delete(test_job)
        db.commit()
        print("✅ Test job deleted")
    else:
        print("❌ Test job not found")
finally:
    db.close()
