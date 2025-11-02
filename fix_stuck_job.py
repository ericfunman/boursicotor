"""
Script to fix stuck job in database
Usage: python fix_stuck_job.py <job_id>
"""
import sys
from datetime import datetime
from backend.models import SessionLocal, DataCollectionJob, JobStatus

def fix_job(job_id: int):
    """Mark a stuck job as completed"""
    db = SessionLocal()
    try:
        job = db.query(DataCollectionJob).filter(DataCollectionJob.id == job_id).first()
        
        if not job:
            print(f"❌ Job {job_id} not found")
            return
        
        print(f"Job {job_id}: {job.ticker_symbol}")
        print(f"  Current status: {job.status.value}")
        print(f"  Progress: {job.progress}%")
        print(f"  Step: {job.current_step}")
        print(f"  Started: {job.started_at}")
        print(f"  Completed: {job.completed_at}")
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            print(f"⚠️  Job is already finished ({job.status.value})")
            return
        
        # Ask for confirmation
        response = input(f"\n💡 Mark job {job_id} as COMPLETED? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Update job
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.current_step = "Completed (manually fixed)"
        job.completed_at = datetime.utcnow()
        
        # Try to get actual record count from database
        try:
            from backend.models import HistoricalData, Ticker
            ticker = db.query(Ticker).filter(Ticker.symbol == job.ticker_symbol).first()
            if ticker:
                total_records = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker.id
                ).count()
                job.records_total = total_records
                print(f"  Found {total_records} records in database")
        except Exception as e:
            print(f"  Could not count records: {e}")
        
        db.commit()
        print(f"✅ Job {job_id} marked as COMPLETED")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def list_stuck_jobs():
    """List all stuck jobs"""
    db = SessionLocal()
    try:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        stuck_jobs = db.query(DataCollectionJob).filter(
            DataCollectionJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
            DataCollectionJob.created_at < cutoff
        ).all()
        
        if not stuck_jobs:
            print("✅ No stuck jobs found")
            return
        
        print(f"\n🔍 Found {len(stuck_jobs)} stuck job(s):\n")
        for job in stuck_jobs:
            print(f"Job {job.id}: {job.ticker_symbol} ({job.source})")
            print(f"  Status: {job.status.value}")
            print(f"  Progress: {job.progress}%")
            print(f"  Created: {job.created_at}")
            print(f"  Step: {job.current_step}")
            print()
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            job_id = int(sys.argv[1])
            fix_job(job_id)
        except ValueError:
            if sys.argv[1] == "list":
                list_stuck_jobs()
            else:
                print("Usage: python fix_stuck_job.py <job_id>")
                print("   or: python fix_stuck_job.py list")
    else:
        print("📋 Listing stuck jobs...")
        list_stuck_jobs()
        print("\nUsage: python fix_stuck_job.py <job_id>")
        print("   or: python fix_stuck_job.py list")
