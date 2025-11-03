#!/usr/bin/env python3
"""
Clean up stuck jobs on startup
"""
from backend.models import SessionLocal, DataCollectionJob, JobStatus

def cleanup_stuck_jobs():
    """Mark any RUNNING jobs as FAILED since they were interrupted"""
    db = SessionLocal()
    try:
        stuck_jobs = db.query(DataCollectionJob).filter(
            DataCollectionJob.status == JobStatus.RUNNING
        ).all()

        for job in stuck_jobs:
            job.status = JobStatus.FAILED
            job.error_message = 'Job cancelled during startup cleanup'
            print(f"Marked job {job.ticker_symbol} as FAILED")

        db.commit()
        print(f"Cleaned up {len(stuck_jobs)} stuck jobs")

    except Exception as e:
        print(f"Error cleaning up jobs: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_stuck_jobs()