#!/usr/bin/env python3
"""
Monitor job progress
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import SessionLocal, DataCollectionJob

def monitor_job(job_id):
    print(f"Monitoring job {job_id}...")
    
    while True:
        db = SessionLocal()
        try:
            job = db.query(DataCollectionJob).filter(DataCollectionJob.id == job_id).first()
            if not job:
                print(f"Job {job_id} not found")
                break
            
            print(f"Status: {job.status.value}, Progress: {job.progress}%, Step: {job.current_step}")
            
            if job.status.value in ['completed', 'failed', 'cancelled']:
                print(f"Final status: {job.status.value}")
                if hasattr(job, 'records_new') and job.records_new is not None:
                    print(f"Records new: {job.records_new}")
                if hasattr(job, 'records_updated') and job.records_updated is not None:
                    print(f"Records updated: {job.records_updated}")
                if hasattr(job, 'records_total') and job.records_total is not None:
                    print(f"Records total: {job.records_total}")
                if job.error_message:
                    print(f"Error: {job.error_message}")
                break
            
        finally:
            db.close()
        
        time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    monitor_job(16)