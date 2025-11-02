#!/usr/bin/env python3
"""
Force delete stuck jobs
"""
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import SessionLocal, DataCollectionJob, JobStatus

db = SessionLocal()
try:
    # Get all running/pending jobs
    stuck_jobs = db.query(DataCollectionJob).filter(
        DataCollectionJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
    ).all()
    
    print(f"Found {len(stuck_jobs)} stuck job(s)")
    
    for job in stuck_jobs:
        print(f"Cancelling job {job.id}: {job.ticker_symbol} ({job.status.value})")
        job.status = JobStatus.CANCELLED
        job.error_message = "Force cancelled - job was stuck"
        job.current_step = "Cancelled by user"
        job.completed_at = datetime.utcnow()
        job.progress = 0
    
    db.commit()
    print(f"✅ Cancelled {len(stuck_jobs)} job(s)")
    
finally:
    db.close()
