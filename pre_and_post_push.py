#!/usr/bin/env python3
"""
Complete pre-and-post-push verification workflow
Usage: python pre_and_post_push.py
"""
import subprocess
import sys
import time

def run_pre_push():
    """Run pre-push verification"""
    print("\n" + "="*70)
    print("[1] PRE-PUSH VERIFICATION")
    print("="*70)
    
    result = subprocess.run(['python', 'verify_before_push.py'])
    if result.returncode != 0:
        print("\nERROR: Pre-push verification failed. Fix errors and try again.")
        return False
    
    return True

def confirm_push():
    """Ask user to confirm push"""
    print("\n" + "="*70)
    print("[OK] LOCAL VERIFICATION PASSED")
    print("="*70)
    
    print("\nReady to push to GitHub!")
    print("   type 'git push' in the terminal to push the changes")
    print("\nAfter pushing, run: python verify_after_push.py")
    print("   to monitor GitHub Actions completion")
    
    return True

if __name__ == "__main__":
    if run_pre_push():
        confirm_push()
        sys.exit(0)
    else:
        sys.exit(1)
