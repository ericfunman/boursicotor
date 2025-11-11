"""
Test script to verify Celery worker restart functionality
"""
from backend.job_manager import JobManager

print("Testing Celery worker restart...")
print("=" * 50)

success = JobManager.restart_celery_worker()

if success:
    print("✅ Worker restart successful!")
    print("\nA new Celery Worker window should have opened.")
    print("Check that it says 'celery@FunOrdi ready.'")
else:
    print("❌ Worker restart failed!")
    print("\nCheck the logs for errors.")

print("=" * 50)
