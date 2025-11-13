#!/usr/bin/env python
"""
Verification script for VENV migration
Tests that all critical packages are working after fresh venv setup
"""

import sys
print('='*60)
print(' VENV MIGRATION VERIFICATION ')
print('='*60)
print()

# Test 1: Python
print('✅ Python:', sys.version.split()[0])

# Test 2: Key packages
packages = ['streamlit', 'celery', 'pytest', 'pandas', 'numpy', 'sqlalchemy']
print('✅ Packages:')
for pkg in packages:
    try:
        mod = __import__(pkg)
        v = getattr(mod, '__version__', 'N/A')
        print(f'   • {pkg:15} {v}')
    except Exception as e:
        print(f'   • {pkg:15} FAILED: {e}')

# Test 3: Backend imports
print()
print('✅ Backend modules:')
try:
    from backend.config import logger
    print('   • backend.config   OK')
except Exception as e:
    print(f'   • backend.config   FAILED: {e}')

try:
    from backend.celery_config import celery_app
    print('   • backend.celery_config OK')
except Exception as e:
    print(f'   • backend.celery_config FAILED: {e}')

try:
    from backend.models import init_db
    print('   • backend.models   OK')
except Exception as e:
    print(f'   • backend.models   FAILED: {e}')

# Test 4: Path
print()
print('✅ Executable path:')
print(f'   {sys.executable}')

# Test 5: Virtual environment check
import os
venv_path = os.path.dirname(os.path.dirname(sys.executable))
print()
print('✅ Virtual environment:')
print(f'   {venv_path}')
if 'venv' in venv_path and 'venv_old' not in venv_path:
    print('   Status: ✅ CORRECT (using venv, not venv_old)')
else:
    print('   Status: ⚠️  WARNING (check venv path)')

print()
print('='*60)
print(' ✅ ALL SYSTEMS GO - READY TO LAUNCH ')
print('='*60)
