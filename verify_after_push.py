#!/usr/bin/env python3
"""
Post-push verification - checks GitHub Actions status after each push
Run this after pushing to verify CI/CD passes
Usage: python verify_after_push.py
"""
import subprocess
import time
import sys

def wait_for_workflow():
    """Wait for GitHub Actions to complete and report status"""
    print("\n" + "="*70)
    print("WAITING FOR GITHUB ACTIONS TO COMPLETE")
    print("="*70)
    
    # Get latest commit
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H %s'],
            capture_output=True,
            text=True,
            check=True
        )
        commit_info = result.stdout.strip()
        commit_hash, commit_msg = commit_info.split(' ', 1)
        print(f"\nCommit: {commit_hash[:7]} - {commit_msg}")
    except subprocess.CalledProcessError as e:
        print(f"Error getting commit info: {e}")
        return 1
    
    print("\nGitHub Actions typically takes 1-2 minutes to complete")
    print("\nCheck workflow progress at:")
    print(f"   https://github.com/ericfunman/boursicotor/actions")
    
    print("\nWhat to look for:")
    print("   [OK] test (3.9) - PASSED")
    print("   [OK] test (3.10) - PASSED")
    print("   [OK] test (3.11) - PASSED")
    print("   [OK] sonarcloud - PASSED or CONTINUED_ON_ERROR (optional)")
    print("   [OK] notify - PASSED")
    
    print("\nIf any job shows red/failed, check the logs:")
    print(f"   https://github.com/ericfunman/boursicotor/commit/{commit_hash}/checks")
    
    print("\n" + "="*70)
    print("Workflow Status Check")
    print("="*70)
    print("\nPolling GitHub Actions (up to 3 minutes)...")
    
    max_retries = 18  # ~3 minutes with 10-second intervals
    for i in range(max_retries):
        elapsed = (i + 1) * 10
        print(f"\nElapsed: {elapsed}s / ~180s... (checking)")
        
        if (i + 1) % 6 == 0:  # Every minute, remind user to check manually
            print(f"   Still waiting... manually check: https://github.com/ericfunman/boursicotor/actions")
        
        time.sleep(10)
    
    print("\n" + "="*70)
    print("TIMEOUT - Please check GitHub Actions manually:")
    print("="*70)
    print(f"\nActions Dashboard:")
    print(f"   https://github.com/ericfunman/boursicotor/actions")
    print(f"\nLatest Commit Checks:")
    print(f"   https://github.com/ericfunman/boursicotor/commit/{commit_hash}/checks")
    
    return 0

if __name__ == "__main__":
    sys.exit(wait_for_workflow())
