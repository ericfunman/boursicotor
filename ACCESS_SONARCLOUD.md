"""
Access SonarCloud results without local token
Multiple approaches to fetch and analyze issues
"""

# ==============================================================
# APPROACH 1: Use GitHub API to trigger SonarCloud via Actions
# ==============================================================

# Check the latest workflow run status:
# https://api.github.com/repos/ericfunman/boursicotor/actions/runs?per_page=1

# Response includes:
# - run status (completed, in_progress)
# - run ID 
# - commit SHA
# - conclusion (success, failure)

# ==============================================================
# APPROACH 2: Direct SonarCloud Web Interface (No auth needed for public)
# ==============================================================

SONAR_URLS = {
    "Dashboard": "https://sonarcloud.io/organizations/ericfunman/projects",
    "Project": "https://sonarcloud.io/project/overview?id=ericfunman_boursicotor",
    "Issues": "https://sonarcloud.io/project/issues?id=ericfunman_boursicotor",
    "Code": "https://sonarcloud.io/project/code?id=ericfunman_boursicotor",
    "Coverage": "https://sonarcloud.io/project/coverage?id=ericfunman_boursicotor",
}

# ==============================================================
# APPROACH 3: Use SonarCloud public API (no auth needed)
# ==============================================================

SONARCLOUD_API_URLS = {
    # Get project status
    "project_status": "https://sonarcloud.io/api/projects/status?projectKey=ericfunman_boursicotor",
    
    # Get metrics (public)
    "measures": "https://sonarcloud.io/api/measures/component?component=ericfunman_boursicotor&metricKeys=coverage,violations,complexity",
    
    # Get issues (might require auth for details)
    "issues_search": "https://sonarcloud.io/api/issues/search?componentKeys=ericfunman_boursicotor&statuses=OPEN",
}

# ==============================================================
# APPROACH 4: Parse GitHub Actions artifact
# ==============================================================

# After workflow completes, SonarCloud generates:
# - coverage.xml artifact
# - sonar-project-dump.json (if available)
# - HTML coverage report

# Download from: https://github.com/ericfunman/boursicotor/actions
# - Click latest run
# - Scroll to "Artifacts"
# - Download coverage report

# ==============================================================
# APPROACH 5: Use curl from terminal
# ==============================================================

CURL_COMMANDS = """
# Get project metrics (NO AUTH NEEDED for public projects)
curl -s "https://sonarcloud.io/api/measures/component?component=ericfunman_boursicotor&metricKeys=coverage,violations,bugs,code_smells,security_hotspots" | python -m json.tool

# Get issues count by type (might work without auth)
curl -s "https://sonarcloud.io/api/issues/search?componentKeys=ericfunman_boursicotor&statuses=OPEN&pageSize=1" | python -m json.tool

# Get project analysis (includes last scan date)
curl -s "https://sonarcloud.io/api/projects/status?projectKey=ericfunman_boursicotor" | python -m json.tool
"""

# ==============================================================
# APPROACH 6: Parse sonarcloud.properties from commit
# ==============================================================

# The ci-cd.yml workflow passes these args to SonarCloud:
# -Dsonar.projectKey=ericfunman_boursicotor
# -Dsonar.organization=ericfunman
# -Dsonar.sources=backend,frontend

# ==============================================================
# BEST APPROACH: Check GitHub Actions logs directly
# ==============================================================

GITHUB_ACTIONS_LOGS = """
Go to: https://github.com/ericfunman/boursicotor/actions

1. Click latest workflow run
2. Scroll to "SonarCloud Scan" step
3. See the output with:
   - Number of issues
   - Quality gate status
   - Coverage %
   - Issue breakdown

Example output to look for:
   "violations":"163"
   "coverage":"5.6%"
   "quality_gate_status":"FAILED"
"""

print("=" * 70)
print("WAYS TO ACCESS SONARCLOUD RESULTS")
print("=" * 70)

print("\n✅ BEST OPTIONS (No token needed):\n")

print("1️⃣  DIRECT WEB - View in browser:")
print("   https://sonarcloud.io/project/overview?id=ericfunman_boursicotor")
print("   https://sonarcloud.io/project/issues?id=ericfunman_boursicotor")

print("\n2️⃣  GITHUB ACTIONS - Check latest run logs:")
print("   https://github.com/ericfunman/boursicotor/actions")
print("   → Latest run → SonarCloud Scan step")

print("\n3️⃣  API CALL (Python) - No auth needed:")
print("   ```python")
print("   import requests")
print("   r = requests.get('https://sonarcloud.io/api/measures/component'")
print("       '?component=ericfunman_boursicotor'")
print("       '&metricKeys=coverage,violations')")
print("   print(r.json())")
print("   ```")

print("\n4️⃣  CURL - Terminal command:")
print("   curl -s 'https://sonarcloud.io/api/measures/component?component=ericfunman_boursicotor&metricKeys=coverage,violations' | python -m json.tool")

print("\n5️⃣  DOWNLOAD - Coverage report from artifacts:")
print("   https://github.com/ericfunman/boursicotor/actions")
print("   → Latest run → Artifacts → coverage reports")

print("\n" + "=" * 70)
print("RECOMMENDED NEXT STEP:")
print("=" * 70)
print("\nGo to GitHub Actions and check the latest 'SonarCloud Scan' step")
print("to see the exact issue breakdown (violations by rule type)")
print("\nThen come back and share the output so I can create targeted fixes!")
