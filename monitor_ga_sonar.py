"""
Monitor GitHub Actions workflow and check Sonar metrics after push
"""
import subprocess
import time
import requests
import json
import sys
from datetime import datetime

# Configuration
GITHUB_REPO = "ericfunman/boursicotor"
GITHUB_TOKEN = None  # Will read from git config
SONAR_TOKEN = None  # Will read from git config
SONAR_ORG = "ericfunman"
SONAR_PROJECT = "ericfunman_boursicotor"

def get_latest_workflow_run():
    """Get the latest workflow run"""
    try:
        # Get GitHub token from git config
        result = subprocess.run(
            ["git", "config", "--global", "github.token"],
            capture_output=True,
            text=True
        )
        token = result.stdout.strip()
        
        if not token:
            print("⚠️  GitHub token not found in git config")
            return None
        
        headers = {"Authorization": f"token {token}"}
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=1"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            runs = response.json().get("workflow_runs", [])
            if runs:
                return runs[0]
        return None
    except Exception as e:
        print(f"❌ Error getting workflow run: {e}")
        return None

def wait_for_workflow_completion(run_id, max_wait_seconds=300):
    """Wait for workflow to complete"""
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["git", "config", "--global", "github.token"],
            capture_output=True,
            text=True
        )
        token = result.stdout.strip()
        
        if not token:
            print("⚠️  GitHub token not found")
            return None
        
        headers = {"Authorization": f"token {token}"}
        
        while time.time() - start_time < max_wait_seconds:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                run = response.json()
                status = run.get("status")
                conclusion = run.get("conclusion")
                
                if status == "completed":
                    return run
                
                elapsed = int(time.time() - start_time)
                print(f"⏳ Workflow running... ({elapsed}s elapsed, {status} / {conclusion})")
                time.sleep(5)
        
        print(f"⏱️  Timeout: Workflow still running after {max_wait_seconds}s")
        return None
    except Exception as e:
        print(f"❌ Error monitoring workflow: {e}")
        return None

def get_sonar_metrics():
    """Get SonarCloud metrics"""
    try:
        # Try to get Sonar token from environment
        import os
        token = os.getenv("SONAR_TOKEN")
        
        if not token:
            print("⚠️  SONAR_TOKEN not found in environment")
            return None
        
        url = f"https://sonarcloud.io/api/measures/component?component={SONAR_PROJECT}&metricKeys=coverage,violations"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("component", {})
        else:
            print(f"⚠️  Sonar API returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting Sonar metrics: {e}")
        return None

def display_workflow_status(run):
    """Display workflow status"""
    print("\n" + "="*60)
    print("📊 WORKFLOW STATUS")
    print("="*60)
    
    if not run:
        print("❌ Could not retrieve workflow information")
        return False
    
    status = run.get("status")
    conclusion = run.get("conclusion")
    name = run.get("name", "Unknown")
    head_branch = run.get("head_branch")
    run_number = run.get("run_number")
    
    print(f"Run: {run_number}")
    print(f"Name: {name}")
    print(f"Branch: {head_branch}")
    print(f"Status: {status}")
    print(f"Conclusion: {conclusion}")
    
    if conclusion == "success":
        print("✅ WORKFLOW PASSED")
        return True
    elif conclusion == "failure":
        print("❌ WORKFLOW FAILED - Check GitHub Actions for details")
        return False
    else:
        print(f"⚠️  Status: {status} ({conclusion})")
        return None

def display_sonar_metrics(component):
    """Display SonarCloud metrics"""
    print("\n" + "="*60)
    print("📈 SONARCLOUD METRICS")
    print("="*60)
    
    if not component:
        print("❌ Could not retrieve SonarCloud metrics")
        print("(Sonar scan may still be running)")
        return
    
    measures = {m["metric"]: m.get("value", "N/A") for m in component.get("measures", [])}
    
    coverage = measures.get("coverage", "N/A")
    violations = measures.get("violations", "N/A")
    
    print(f"Coverage: {coverage}%")
    print(f"Violations: {violations}")
    
    if coverage != "N/A":
        try:
            cov_val = float(coverage)
            if cov_val >= 60:
                print("✅ Coverage target (60%) REACHED")
            elif cov_val >= 20:
                print(f"⚠️  Coverage at {cov_val}% - Target is 60%")
            else:
                print(f"❌ Coverage at {cov_val}% - Need to boost tests")
        except:
            pass

def main():
    print("\n" + "="*60)
    print("🔍 GITHUB ACTIONS & SONARCLOUD MONITOR")
    print("="*60)
    
    # Get latest workflow run
    print("\n📍 Fetching latest workflow run...")
    run = get_latest_workflow_run()
    
    if not run:
        print("⚠️  Could not get workflow information")
        print("(GitHub token may not be configured)")
        print("To set up: git config --global github.token YOUR_TOKEN")
        return
    
    run_id = run.get("id")
    print(f"✓ Found run #{run.get('run_number')} (ID: {run_id})")
    
    # Display current status
    display_workflow_status(run)
    
    # Wait for completion if still running
    status = run.get("status")
    if status != "completed":
        print("\n⏳ Workflow still running - waiting for completion...")
        print("(Timeout: 5 minutes)")
        run = wait_for_workflow_completion(run_id)
        
        if run:
            display_workflow_status(run)
    
    # Try to get Sonar metrics
    print("\n📍 Fetching SonarCloud metrics...")
    time.sleep(2)  # Wait a bit for Sonar to update
    component = get_sonar_metrics()
    display_sonar_metrics(component)
    
    # Summary
    print("\n" + "="*60)
    print("📋 NEXT STEPS")
    print("="*60)
    print("1. Check GitHub Actions: https://github.com/ericfunman/boursicotor/actions")
    print("2. Check SonarCloud: https://sonarcloud.io/organizations/ericfunman/projects")
    print("3. If coverage < 60%: Create more targeted tests")
    print("4. If violations > 0: Fix Sonar issues or add to ignore list")

if __name__ == "__main__":
    main()
