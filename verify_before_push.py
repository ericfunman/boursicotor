#!/usr/bin/env python3
"""
Pre-commit verification script - runs before each push
Validates that tests pass and code is ready for deployment
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"[*] {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"\n[ERROR] FAILED: {description}")
        return False
    
    print(f"\n[OK] PASSED: {description}")
    return True

def main():
    """Run all verification checks"""
    checks = [
        ("pytest tests/test_security.py -v", "Run Unit Tests"),
        ("python -m py_compile backend/data_collector.py backend/data_interpolator.py backend/job_manager.py backend/technical_indicators.py frontend/app.py", "Verify Python Syntax"),
    ]
    
    failed_checks = []
    
    for cmd, desc in checks:
        if not run_command(cmd, desc):
            failed_checks.append(desc)
    
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    if failed_checks:
        print(f"\n[ERROR] {len(failed_checks)} check(s) failed:")
        for check in failed_checks:
            print(f"   - {check}")
        print("\nDO NOT PUSH - Fix errors above first!")
        return 1
    
    print("\n[OK] All checks passed!")
    print("Ready to push to GitHub")
    print("\nAfter push, check GitHub Actions:")
    print("   https://github.com/ericfunman/boursicotor/actions")
    print("   (may take 1-2 minutes to complete)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
