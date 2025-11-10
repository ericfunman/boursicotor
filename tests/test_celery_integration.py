"""
Test script to verify Celery integration
"""

def test_imports():
    """Test that all necessary modules can be imported"""
    print("Testing imports...")
    
    try:
        from backend.models import DataCollectionJob, JobStatus
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    try:
        from backend.job_manager import JobManager
        print("✅ JobManager imported successfully")
    except Exception as e:
        print(f"❌ Failed to import JobManager: {e}")
        return False
    
    try:
        from backend.celery_config import celery_app
        print("✅ Celery app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Celery app: {e}")
        return False
    
    try:
        from backend.tasks import collect_data_ibkr, collect_data_yahoo, cleanup_old_jobs
        print("✅ Tasks imported successfully")
    except Exception as e:
        print(f"❌ Failed to import tasks: {e}")
        return False
    
    return True


def test_database():
    """Test that database tables exist"""
    print("\nTesting database...")
    
    try:
        from backend.models import SessionLocal, DataCollectionJob
        from sqlalchemy import inspect
        
        db = SessionLocal()
        inspector = inspect(db.bind)
        
        if 'data_collection_jobs' in inspector.get_table_names():
            print("✅ data_collection_jobs table exists")
            
            # Check if table is accessible
            count = db.query(DataCollectionJob).count()
            print(f"✅ Table accessible, {count} jobs found")
        else:
            print("❌ data_collection_jobs table does not exist")
            print("Run: python -c 'from backend.models import init_db; init_db()'")
            return False
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_job_manager():
    """Test JobManager functionality"""
    print("\nTesting JobManager...")
    
    try:
        from backend.job_manager import JobManager
        
        manager = JobManager()
        
        # Test statistics
        stats = manager.get_statistics()
        print(f"✅ Statistics retrieved: {stats}")
        
        # Test get recent jobs
        jobs = manager.get_recent_jobs(limit=5)
        print(f"✅ Recent jobs retrieved: {len(jobs)} jobs")
        
        return True
    
    except Exception as e:
        print(f"❌ JobManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Celery Integration Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Imports
    if not test_imports():
        all_passed = False
        print("\n⚠️ Some imports failed. Have you installed requirements_celery.txt?")
        print("   Run: pip install -r requirements_celery.txt")
    
    # Test 2: Database
    if not test_database():
        all_passed = False
        print("\n⚠️ Database test failed. Have you run init_db()?")
        print("   Run: python -c 'from backend.models import init_db; init_db()'")
    
    # Test 3: JobManager
    if not test_job_manager():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Start Redis: redis-server")
        print("2. Start Celery worker: celery -A backend.celery_config worker --loglevel=info --pool=solo")
        print("3. Start Streamlit: streamlit run frontend/app.py")
        print("4. (Optional) Start Flower: celery -A backend.celery_config flower")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the issues above before continuing.")
    print("=" * 60)
