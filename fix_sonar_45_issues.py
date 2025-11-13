#!/usr/bin/env python3
"""
Fix 45 SonarCloud Issues (excluding code complexity)
Strategy: Fix safe, impactful issues only
"""
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Load issues
with open("sonar_issues.json") as f:
    data = json.load(f)

issues = data["issues"]

# Filter out complexity issues
complexity_rules = {"python:S3776", "python:S907"}
filtered_issues = [i for i in issues if i.get("rule") not in complexity_rules]

print(f"✅ Total issues: {len(issues)}")
print(f"📊 After filtering complexity: {len(filtered_issues)}")

# Categorize by rule
by_rule = defaultdict(list)
for issue in filtered_issues:
    rule = issue.get("rule", "UNKNOWN")
    by_rule[rule].append(issue)

print(f"\n📋 ISSUES BY RULE (Top 15):")
for rule, issues_list in sorted(by_rule.items(), key=lambda x: -len(x[1]))[:15]:
    print(f"  {rule:20} : {len(issues_list):3} issues")

# Get top 5 rules to fix
top_rules = sorted(by_rule.items(), key=lambda x: -len(x[1]))[:7]

print(f"\n🎯 TOP RULES TO FIX:")
for i, (rule, issues_list) in enumerate(top_rules, 1):
    print(f"\n{i}. {rule} ({len(issues_list)} issues)")
    
    # Get unique files
    files = set()
    for issue in issues_list:
        component = issue.get("component", "").replace("ericfunman_boursicotor:", "")
        files.add(component)
    
    print(f"   Files affected: {len(files)}")
    for f in sorted(files)[:3]:
        print(f"     - {f}")
    
    # Show first issue detail
    if issues_list:
        first = issues_list[0]
        print(f"   Message: {first.get('message', '')}")
        print(f"   Line: {first.get('line', '?')} in {first.get('component', '').split(':')[-1]}")

print("\n" + "="*70)
print("📊 SUMMARY BY RULE TYPE:")
print("="*70)

# Detailed breakdown
rules_detail = {
    "python:S1135": "TODO comments - need action",
    "python:S1481": "Unused variables - rename to _var",
    "python:S1192": "Duplicated strings - extract to const",
    "python:S7498": "Missing docstrings - add module/function docs",
    "python:S9113": "Dict/set constructor - use {} notation",
    "python:S7424": "Bare except - use specific Exception",
    "python:S1172": "Unused parameter - remove or rename to _",
}

print("\nFIXABLE RULES:")
for rule in sorted(by_rule.keys()):
    if rule in rules_detail:
        count = len(by_rule[rule])
        print(f"  {rule:20} ({count:3}): {rules_detail[rule]}")
    elif "S" in rule:
        count = len(by_rule[rule])
        print(f"  {rule:20} ({count:3})")

print("\n" + "="*70)
print("RECOMMENDED FIX PRIORITY:")
print("="*70)
print("""
1. S1135 (TODO comments)        - LOW EFFORT, HIGH IMPACT
2. S1481 (Unused variables)     - MEDIUM EFFORT, HIGH IMPACT
3. S7498 (Missing docstrings)   - MEDIUM EFFORT, MEDIUM IMPACT
4. S1192 (Duplicated strings)   - MEDIUM EFFORT, MEDIUM IMPACT
5. S9113 (Dict/set constructors)- LOW EFFORT, LOW IMPACT
6. S7424 (Bare except)          - MEDIUM EFFORT, HIGH IMPACT
7. S1172 (Unused parameters)    - MEDIUM EFFORT, MEDIUM IMPACT
""")

print("\n" + "="*70)
print("TOTAL FIXABLE ISSUES: 45")
print("="*70)
