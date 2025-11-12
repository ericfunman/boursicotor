#!/usr/bin/env python3
"""
Fetch detailed Sonar issues from public API
"""
import requests
import json

PROJECT_KEY = "ericfunman_boursicotor"
BASE_URL = "https://sonarcloud.io/api"

def get_issues_by_rule():
    """Get issues grouped by rule type"""
    
    # Try to get issues (might be limited without auth)
    url = f"{BASE_URL}/issues/search"
    
    issues_by_rule = {}
    page = 1
    
    while True:
        params = {
            "componentKeys": PROJECT_KEY,
            "statuses": "OPEN",
            "ps": 500,  # page size
            "p": page
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])
                
                if not issues:
                    break
                
                for issue in issues:
                    rule = issue.get("rule", "UNKNOWN")
                    if rule not in issues_by_rule:
                        issues_by_rule[rule] = []
                    
                    issues_by_rule[rule].append({
                        "file": issue.get("component", "").split(":")[-1],
                        "line": issue.get("line", 0),
                        "message": issue.get("message", ""),
                        "severity": issue.get("severity", ""),
                    })
                
                total = data.get("total", 0)
                print(f"Fetched {len(issues)} issues (page {page}, total: {total})")
                
                if len(issues) < 500:
                    break
                    
                page += 1
            else:
                print(f"API returned {response.status_code}")
                break
                
        except Exception as e:
            print(f"Error: {e}")
            break
    
    return issues_by_rule

if __name__ == "__main__":
    print("=" * 80)
    print("FETCHING SONAR ISSUES DETAILS")
    print("=" * 80)
    
    issues = get_issues_by_rule()
    
    print(f"\n{'=' * 80}")
    print("ISSUES BY RULE")
    print("=" * 80)
    
    for rule in sorted(issues.keys(), key=lambda r: len(issues[r]), reverse=True):
        count = len(issues[rule])
        print(f"\n{rule}: {count} issues")
        
        # Show first 5 examples
        for i, issue in enumerate(issues[rule][:5]):
            print(f"  [{i+1}] {issue['file']}:{issue['line']} - {issue['message'][:80]}")
        
        if count > 5:
            print(f"  ... and {count - 5} more")
    
    # Save to file
    with open("sonar_issues_detailed.json", "w") as f:
        json.dump(issues, f, indent=2)
    
    print(f"\n✅ Saved detailed issues to sonar_issues_detailed.json")
    print(f"Total issues: {sum(len(v) for v in issues.values())}")
