#!/usr/bin/env python3
"""
Extract S1192 duplicated strings from sonar_45_issues.json and identify patterns
"""
import json

with open("sonar_45_issues.json") as f:
    data = json.load(f)

issues = data["issues"]
s1192_issues = [i for i in issues if i.get("rule") == "python:S1192"]

print("=" * 80)
print("📋 S1192 - DUPLICATED STRING LITERALS (9 issues)")
print("=" * 80)

# Group by file
by_file = {}
for issue in s1192_issues:
    component = issue.get("component", "").replace("ericfunman_boursicotor:", "")
    line = issue.get("line", 0)
    msg = issue.get("message", "")
    
    if component not in by_file:
        by_file[component] = []
    
    by_file[component].append({
        "line": line,
        "message": msg,
        "flows": issue.get("flows", [])
    })

for file_path in sorted(by_file.keys()):
    issues_list = by_file[file_path]
    print(f"\n{file_path} ({len(issues_list)} duplications)")
    
    for issue_item in issues_list:
        line = issue_item["line"]
        msg = issue_item["message"]
        flows = issue_item.get("flows", [])
        
        print(f"  Line {line}: {msg[:70]}")
        
        # Show duplication locations
        if flows:
            for flow in flows:
                for loc in flow.get("locations", []):
                    dup_line = loc.get("textRange", {}).get("startLine", "?")
                    print(f"    → Duplicate at line {dup_line}")

print("\n" + "=" * 80)
print("💡 RECOMMENDATION:")
print("=" * 80)
print("""
For backend/ibkr_collector.py (9 duplications):
- Extract ' Europe/Paris' to TIMEZONE_PARIS = ' Europe/Paris'
- Extract other common strings to module-level constants

Expected to fix: All 9 S1192 issues
""")
