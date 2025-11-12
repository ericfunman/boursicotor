"""
Fetch and analyze Sonar issues from SonarCloud
"""
import requests
import json
from collections import Counter
import os

SONAR_ORG = "ericfunman"
SONAR_PROJECT = "ericfunman_boursicotor"
SONAR_TOKEN = os.getenv("SONAR_TOKEN")

def fetch_all_issues():
    """Fetch all OPEN issues from SonarCloud"""
    
    if not SONAR_TOKEN:
        print("❌ SONAR_TOKEN not set in environment")
        return []
    
    url = f"https://sonarcloud.io/api/issues/search"
    params = {
        "componentKeys": SONAR_PROJECT,
        "statuses": "OPEN",
        "pageSize": 500,
        "p": 1
    }
    headers = {"Authorization": f"Bearer {SONAR_TOKEN}"}
    
    all_issues = []
    
    try:
        while True:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Sonar API error: {response.status_code}")
                break
            
            data = response.json()
            issues = data.get("issues", [])
            
            if not issues:
                break
            
            all_issues.extend(issues)
            
            total = data.get("total", 0)
            print(f"📊 Fetched {len(all_issues)}/{total} issues...")
            
            if len(all_issues) >= total:
                break
            
            params["p"] += 1
    
    except Exception as e:
        print(f"❌ Error fetching issues: {e}")
    
    return all_issues

def analyze_issues(issues):
    """Analyze and categorize issues"""
    
    print(f"\n{'='*60}")
    print(f"📈 SONAR ISSUES ANALYSIS")
    print(f"{'='*60}")
    print(f"Total OPEN issues: {len(issues)}\n")
    
    # Group by rule
    rules = Counter()
    files_affected = Counter()
    
    rule_details = {}  # rule -> list of issues
    
    for issue in issues:
        rule = issue.get("rule", "UNKNOWN")
        file_path = issue.get("component", "").replace(f"{SONAR_PROJECT}:", "")
        
        rules[rule] += 1
        files_affected[file_path] += 1
        
        if rule not in rule_details:
            rule_details[rule] = []
        rule_details[rule].append({
            "file": file_path,
            "line": issue.get("line", "?"),
            "message": issue.get("message", ""),
            "severity": issue.get("severity", ""),
            "type": issue.get("type", "")
        })
    
    # Show top rules
    print("📋 TOP RULES (by count):")
    print("-" * 60)
    for rule, count in rules.most_common(15):
        print(f"  {rule:20} : {count:4} issues")
    
    # Show affected files
    print(f"\n📁 FILES WITH MOST ISSUES:")
    print("-" * 60)
    for file_path, count in files_affected.most_common(10):
        print(f"  {count:3} issues : {file_path}")
    
    # Detailed breakdown for top 5 rules
    print(f"\n📝 DETAILED BREAKDOWN (Top 5 rules):")
    print("-" * 60)
    
    for rule, count in rules.most_common(5):
        print(f"\n{rule} ({count} issues):")
        
        # Group by severity
        severity_map = Counter()
        for issue in rule_details[rule]:
            severity_map[issue["severity"]] += 1
        
        print(f"  Severity: {dict(severity_map)}")
        
        # Show first 3 examples
        print(f"  Examples:")
        for i, issue in enumerate(rule_details[rule][:3]):
            print(f"    [{i+1}] {issue['file']}:{issue['line']}")
            print(f"        {issue['message'][:80]}")
    
    return rules, files_affected, rule_details

def generate_fix_plan(rules, rule_details):
    """Generate a plan to fix issues"""
    
    print(f"\n{'='*60}")
    print(f"🛠️  FIX STRATEGY")
    print(f"{'='*60}\n")
    
    priority_mapping = {
        "S1192": ("HIGH", "Duplicated strings - extract to constants"),
        "S7498": ("HIGH", "dict() literal - use {} instead"),
        "S3776": ("MEDIUM", "Cognitive complexity - refactor methods"),
        "S1481": ("MEDIUM", "Unused variables - remove them"),
        "S117": ("MEDIUM", "Naming convention - rename variables"),
        "S1172": ("LOW", "Unused parameter - add _prefix or remove"),
        "S5886": ("LOW", "Expression complexity - simplify"),
        "S3358": ("LOW", "Boolean logic - simplify conditions"),
    }
    
    print("PRIORITY ORDER FOR FIXES:\n")
    
    for rule in sorted(rules.keys(), key=lambda r: rules[r], reverse=True):
        count = rules[rule]
        priority, description = priority_mapping.get(rule, ("LOW", "Other issue"))
        
        print(f"{rule:12} ({count:3} issues) [{priority:6}] - {description}")
    
    # Calculate estimated effort
    total_high = sum(c for rule, c in rules.items() if rule in ["S1192", "S7498"])
    total_medium = sum(c for rule, c in rules.items() if rule in ["S3776", "S1481", "S117"])
    
    print(f"\n📊 EFFORT ESTIMATE:")
    print(f"  HIGH priority:   {total_high:3} issues (automated fixes possible)")
    print(f"  MEDIUM priority: {total_medium:3} issues (manual review needed)")
    print(f"  LOW priority:    {len(issues) - total_high - total_medium:3} issues (nice-to-fix)")

if __name__ == "__main__":
    print("🔄 Fetching Sonar issues...\n")
    issues = fetch_all_issues()
    
    if issues:
        rules, files, details = analyze_issues(issues)
        generate_fix_plan(rules, details)
        
        # Save to file for reference
        with open("sonar_issues_analysis.json", "w") as f:
            json.dump({
                "total": len(issues),
                "rules": dict(rules),
                "files": dict(files),
                "issues": issues[:50]  # Save first 50 for reference
            }, f, indent=2)
        
        print(f"\n✅ Analysis saved to sonar_issues_analysis.json")
    else:
        print("⚠️  No issues found or unable to fetch")
