#!/usr/bin/env python3
"""
GitHub Actions Status Reporter
Provides action items to check GitHub Actions status
"""
import subprocess
import sys

def get_latest_commit():
    """Get latest commit hash"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H %s'],
            capture_output=True,
            text=True,
            check=True
        )
        parts = result.stdout.strip().split(' ', 1)
        if len(parts) == 2:
            return parts[0][:7], parts[1]
        return result.stdout.strip()[:7], "unknown"
    except:
        return "unknown", "unknown"

def main():
    commit_hash, commit_msg = get_latest_commit()
    
    print("\n" + "="*70)
    print("GITHUB ACTIONS STATUS CHECKER")
    print("="*70)
    
    print(f"\nLatest commit: {commit_hash} - {commit_msg}")
    
    print("\n" + "="*70)
    print("WHAT TO CHECK")
    print("="*70)
    
    print("\n1. ACTIONS DASHBOARD:")
    print("   https://github.com/ericfunman/boursicotor/actions")
    print("   (Find the latest run with commit message above)")
    
    print("\n2. DIRECT COMMIT CHECKS:")
    print(f"   https://github.com/ericfunman/boursicotor/commit/{commit_hash}/checks")
    
    print("\n3. EXPECTED JOBS (should all show checkmarks):")
    print("   [+] test (3.9)")
    print("   [+] test (3.10)")
    print("   [+] test (3.11)")
    print("   [+] sonarcloud (optional)")
    print("   [+] notify")
    
    print("\n4. IF FAILED, CHECK LOG:")
    print("   Click on the failed job name to see full output")
    
    print("\n5. KEY INDICATORS:")
    print("   GREEN = Success (workflow passed)")
    print("   RED = Failed (investigate logs)")
    print("   YELLOW = Warning (usually optional, can continue)")
    
    print("\n" + "="*70)
    print("STATUS SUMMARY SCRIPT")
    print("="*70)
    
    print("\nTo see the EXACT status, you need to:")
    print("1. Go to https://github.com/ericfunman/boursicotor/actions")
    print("2. Find your latest commit")
    print("3. Check if ALL jobs show green checkmarks")
    
    print("\nThis script cannot directly check GitHub API")
    print("(would require authentication token)")
    
    print("\n" + "="*70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
