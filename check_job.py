#!/usr/bin/env python3
"""
Check job status
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import SessionLocal, DataCollectionJob

print("Waiting 30 seconds for job to process...")
time.sleep(30)

db = SessionLocal()
try:
    job = db.query(DataCollectionJob).filter(DataCollectionJob.id == 15).first()
    if job:
        print(f"Job 15 status: {job.status.value}")
        print(f"Progress: {job.progress}%")
        print(f"Step: {job.current_step}")
        if job.error_message:
            print(f"Error: {job.error_message}")
        if hasattr(job, 'records_new') and job.records_new is not None:
            print(f"Records new: {job.records_new}")
        if hasattr(job, 'records_updated') and job.records_updated is not None:
            print(f"Records updated: {job.records_updated}")
        if hasattr(job, 'records_total') and job.records_total is not None:
            print(f"Records total: {job.records_total}")
    else:
        print("Job 15 not found")
finally:
    db.close()