#!/usr/bin/env python3
"""
Fetch exactly 45 SonarCloud issues (excluding code complexity)
"""
import requests
import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

SONAR_HOST = "https://sonarcloud.io"
SONAR_PROJECT = "ericfunman_boursicotor"
SONAR_TOKEN = None  # No token needed for public projects

def fetch_sonar_issues() -> List[Dict]:
    """Fetch all OPEN issues from SonarCloud (excluding complexity)"""
    
    print("🔍 Fetching issues from SonarCloud...")
    
    api_url = f"{SONAR_HOST}/api/issues/search"
    
    # Exclude complexity rules and bugs
    exclude_rules = "python:S3776,python:S907,pythonbugs:*"
    
    all_issues = []
    page = 1
    page_size = 100
    
    try:
        while True:
            params = {
                "componentKeys": SONAR_PROJECT,
                "types": "CODE_SMELL,BUG,VULNERABILITY",
                "statuses": "OPEN",
                "ps": page_size,
                "p": page,
            }
            
            print(f"  Page {page}...", end="", flush=True)
            response = requests.get(api_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get("issues", [])
            if not issues:
                print(" Done!")
                break
            
            # Filter out excluded rules
            for issue in issues:
                rule = issue.get("rule", "")
                # Skip complexity and bugs
                if not any(excl in rule for excl in ["S3776", "S907", "pythonbugs"]):
                    all_issues.append(issue)
            
            print(f" +{len(issues)}")
            
            # Safety check
            if len(all_issues) >= 100:
                break
                
            page += 1
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
    
    print(f"\n✅ Total issues fetched: {len(all_issues)}")
    return all_issues[:45]  # Return only 45

def analyze_and_print(issues: List[Dict]):
    """Analyze the 45 issues"""
    
    print("\n" + "="*80)
    print("📊 45 SONARCLOUD ISSUES - DETAILED BREAKDOWN")
    print("="*80)
    
    # Group by rule
    by_rule = defaultdict(list)
    for issue in issues:
        rule = issue.get("rule", "UNKNOWN")
        by_rule[rule].append(issue)
    
    print(f"\n📋 ISSUES BY RULE:")
    print(f"{'Rule':<20} {'Count':<6} {'Severity':<10} {'Description'}")
    print("-" * 80)
    
    rule_descriptions = {
        "python:S1135": "TODO comments",
        "python:S1481": "Unused local variables",
        "python:S1172": "Unused method parameters",
        "python:S7498": "Missing docstrings",
        "python:S117": "Invalid parameter names",
        "python:S125": "Commented out code",
        "python:S3457": "Non-literal in f-string",
        "python:S107": "Too many parameters",
        "python:S5713": "Missing random seed",
        "python:S3358": "Complex ternary operator",
        "python:S5886": "Duplication",
        "python:S1066": "Unused code paths",
        "python:S7504": "Return type annotation",
        "python:S1192": "Duplicated string literals",
        "pythonbugs:S2589": "Boolean literal",
    }
    
    for rule, issues_list in sorted(by_rule.items(), key=lambda x: -len(x[1])):
        severity = issues_list[0].get("severity", "?")
        desc = rule_descriptions.get(rule, rule)
        print(f"{rule:<20} {len(issues_list):<6} {severity:<10} {desc}")
    
    print("\n" + "="*80)
    print("📍 ISSUES BY FILE:")
    print("="*80)
    
    by_file = defaultdict(list)
    for issue in issues:
        component = issue.get("component", "").replace(f"{SONAR_PROJECT}:", "")
        by_file[component].append(issue)
    
    for file_path, file_issues in sorted(by_file.items(), key=lambda x: -len(x[1])):
        print(f"\n{file_path} ({len(file_issues)} issues)")
        for issue in file_issues[:3]:
            rule = issue.get("rule", "?")
            line = issue.get("line", "?")
            msg = issue.get("message", "")[:50]
            print(f"  L{line:4} [{rule}] {msg}...")
        if len(file_issues) > 3:
            print(f"  ... +{len(file_issues)-3} more")
    
    print("\n" + "="*80)
    print(f"✅ TOTAL: {len(issues)} issues")
    print("="*80)
    
    return issues

if __name__ == "__main__":
    issues = fetch_sonar_issues()
    if issues:
        analyze_and_print(issues)
        
        # Save to JSON
        with open("sonar_45_issues.json", "w") as f:
            json.dump({
                "total": len(issues),
                "issues": issues
            }, f, indent=2)
        print(f"\n💾 Saved to sonar_45_issues.json")
    else:
        print("❌ No issues fetched")
