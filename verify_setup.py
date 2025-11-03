"""
Quick verification script to check if Boursicotor is properly set up
"""
import sys
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version: {version.major}.{version.minor}.{version.micro} (requires 3.10+)")
        return False


def check_imports():
    """Check if required packages are installed"""
    required_packages = [
        ('streamlit', 'Streamlit'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('psycopg2', 'psycopg2'),
        ('plotly', 'Plotly'),
        ('sklearn', 'scikit-learn'),
        ('xgboost', 'XGBoost'),
        ('ib_insync', 'ib-insync'),
        ('dotenv', 'python-dotenv'),
        ('loguru', 'Loguru'),
    ]
    
    all_ok = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - not installed")
            all_ok = False
    
    # Optional packages
    optional_packages = [
        ('talib', 'TA-Lib'),
        ('pandas_ta', 'pandas-ta'),
    ]
    
    print("\nOptional packages:")
    for package, name in optional_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"⚠️  {name} - not installed (optional)")
    
    return all_ok


def check_directories():
    """Check if required directories exist"""
    base_dir = Path(__file__).parent
    required_dirs = [
        'backend',
        'frontend',
        'brokers',
        'strategies',
        'backtesting',
        'ml_models',
        'database',
        'utils',
        'examples',
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - missing")
            all_ok = False
    
    return all_ok


def check_config_files():
    """Check if configuration files exist"""
    base_dir = Path(__file__).parent
    config_files = [
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md',
        'INSTALLATION.md',
    ]
    
    all_ok = True
    for file_name in config_files:
        file_path = base_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - missing")
            all_ok = False
    
    # Check .env
    env_path = base_dir / '.env'
    if env_path.exists():
        print(f"✅ .env (configured)")
    else:
        print(f"⚠️  .env - not configured (copy from .env.example)")
    
    return all_ok


def check_database_connection():
    """Try to connect to database"""
    try:
        from backend.config import DATABASE_URL
        from sqlalchemy import create_engine
        
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running and .env is configured")
        return False


def main():
    print("=" * 60)
    print("🔍 Boursicotor Setup Verification")
    print("=" * 60)
    
    results = {}
    
    print("\n📦 Checking Python version...")
    results['python'] = check_python_version()
    
    print("\n📚 Checking required packages...")
    results['packages'] = check_imports()
    
    print("\n📁 Checking directory structure...")
    results['directories'] = check_directories()
    
    print("\n📄 Checking configuration files...")
    results['config'] = check_config_files()
    
    print("\n🗄️  Checking database connection...")
    results['database'] = check_database_connection()
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    
    for check, status in results.items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        print(f"{check.capitalize():20s}: {status_str}")
    
    print("\n" + "=" * 60)
    print(f"Score: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All checks passed! You're ready to use Boursicotor!")
        print("\nNext steps:")
        print("1. Start TWS or IB Gateway")
        print("2. Run: streamlit run frontend/app.py")
        print("3. Or run: start.bat")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Configure .env: copy .env.example .env")
        print("3. Create database: CREATE DATABASE boursicotor;")
        print("4. Initialize database: python database/init_db.py")
    
    print()


if __name__ == "__main__":
    main()
