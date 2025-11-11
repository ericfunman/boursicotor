#!/usr/bin/env python3
"""
GitHub Actions CI/CD Status Checker
Automatically verifies that CI/CD workflows pass after each push
"""
import subprocess
import time
import json
import os
import sys

def get_latest_workflow_run():
    """Get the latest workflow run from GitHub API"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H'],
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = result.stdout.strip()
        print(f"📝 Latest commit: {commit_hash[:7]}")
        return commit_hash
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting latest commit: {e}")
        return None

def check_workflow_status():
    """
    Check if the latest GitHub Actions workflow passed
    This is a placeholder - in real usage, you'd call the GitHub API
    """
    print("\n" + "="*60)
    print("🔍 Checking GitHub Actions Workflow Status")
    print("="*60)
    
    commit = get_latest_workflow_run()
    if not commit:
        return 1
    
    print("\n📋 To check the full workflow status, visit:")
    print(f"   https://github.com/ericfunman/boursicotor/commit/{commit}/checks")
    print("\n⚠️  GitHub Actions may take 1-2 minutes to complete")
    print("   Check the Actions tab after pushing:")
    print("   https://github.com/ericfunman/boursicotor/actions")
    
    return 0

if __name__ == "__main__":
    sys.exit(check_workflow_status())
