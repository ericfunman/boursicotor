#!/usr/bin/env python3
"""
Fix 45 SonarCloud Issues - Detailed Action Plan
Focus on fixable issues excluding S6711 (numpy) and complexity
"""
import json
from pathlib import Path
from collections import defaultdict

# Load issues
with open("sonar_issues.json") as f:
    data = json.load(f)

issues = data["issues"]

# Exclude S6711 (numpy - requires large refactor) and complexity
exclude_rules = {"python:S6711", "python:S3776", "python:S907"}
target_issues = [i for i in issues if i.get("rule") not in exclude_rules]

print("=" * 80)
print("🎯 45 FIXABLE SONARCLOUD ISSUES - DETAILED PLAN")
print("=" * 80)

# Group by rule
by_rule = defaultdict(list)
for issue in target_issues:
    rule = issue.get("rule", "UNKNOWN")
    by_rule[rule].append(issue)

# Define fixes
fixes = {
    "python:S7498": {
        "name": "Missing docstrings",
        "count": len(by_rule.get("python:S7498", [])),
        "effort": "MEDIUM",
        "action": "Add module-level and function docstrings to frontend/app.py and others",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S7498", [])])
    },
    "python:S3457": {
        "name": "Non-literal in f-string",
        "count": len(by_rule.get("python:S3457", [])),
        "effort": "LOW",
        "action": "Remove unnecessary f-string prefixes or add placeholders",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S3457", [])])
    },
    "python:S1481": {
        "name": "Unused local variable",
        "count": len(by_rule.get("python:S1481", [])),
        "effort": "LOW",
        "action": "Rename unused vars to _ or _var_name",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S1481", [])])
    },
    "python:S117": {
        "name": "Invalid parameter name (camelCase)",
        "count": len(by_rule.get("python:S117", [])),
        "effort": "MEDIUM",
        "action": "Rename camelCase parameters to snake_case (IBKR API compatibility issue)",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S117", [])])
    },
    "python:S125": {
        "name": "Commented out code",
        "count": len(by_rule.get("python:S125", [])),
        "effort": "LOW",
        "action": "Remove commented code blocks",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S125", [])])
    },
    "python:S107": {
        "name": "Too many function parameters",
        "count": len(by_rule.get("python:S107", [])),
        "effort": "HIGH",
        "action": "Refactor methods with >13 parameters into dataclass or dict",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S107", [])])
    },
    "python:S1172": {
        "name": "Unused method parameter",
        "count": len(by_rule.get("python:S1172", [])),
        "effort": "MEDIUM",
        "action": "Remove unused parameters from method signatures",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S1172", [])])
    },
    "python:S1135": {
        "name": "TODO comment",
        "count": len(by_rule.get("python:S1135", [])),
        "effort": "MEDIUM",
        "action": "Complete tasks or remove TODO comments",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S1135", [])])
    },
    "python:S5713": {
        "name": "Random seed missing",
        "count": len(by_rule.get("python:S5713", [])),
        "effort": "LOW",
        "action": "Set random seed before using random functions",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S5713", [])])
    },
    "python:S3358": {
        "name": "Ternary operator too complex",
        "count": len(by_rule.get("python:S3358", [])),
        "effort": "MEDIUM",
        "action": "Replace complex ternary with if/elif/else",
        "files": set([i.get("component", "").replace("ericfunman_boursicotor:", "") 
                      for i in by_rule.get("python:S3358", [])])
    },
}

# Print summary
total_fixable = 0
print("\n📋 PRIORITY ORDER (HIGH IMPACT, MEDIUM EFFORT FIRST):\n")

priority_order = [
    "python:S1481",  # Unused vars - easy
    "python:S3457",  # f-string - easy
    "python:S125",   # Commented code - easy
    "python:S5713",  # Random seed - easy
    "python:S1135",  # TODO - easy
    "python:S1172",  # Unused params - medium
    "python:S117",   # Parameter names - medium (IBKR compatibility)
    "python:S7498",  # Docstrings - medium
    "python:S3358",  # Ternary - medium
    "python:S107",   # Too many params - hard
]

for i, rule in enumerate(priority_order, 1):
    if rule in fixes:
        fix = fixes[rule]
        if fix["count"] > 0:
            total_fixable += fix["count"]
            print(f"{i}. {fix['name']:35} ({fix['count']:3} issues) - {fix['effort']:6}")
            print(f"   Action: {fix['action']}")
            print(f"   Files: {', '.join(sorted(fix['files'])[:3])}" + 
                  (f" +{len(fix['files'])-3} more" if len(fix['files']) > 3 else ""))
            print()

print("=" * 80)
print(f"TOTAL FIXABLE ISSUES: {total_fixable}")
print("=" * 80)

# Show distribution
print("\n📊 EFFORT DISTRIBUTION:")
low = sum(f["count"] for f in fixes.values() if f["effort"] == "LOW")
medium = sum(f["count"] for f in fixes.values() if f["effort"] == "MEDIUM")
high = sum(f["count"] for f in fixes.values() if f["effort"] == "HIGH")

print(f"  LOW effort:    {low:3} issues (5-15 min each) = {low*10} min")
print(f"  MEDIUM effort: {medium:3} issues (15-30 min each) = {medium*20} min")
print(f"  HIGH effort:   {high:3} issues (30+ min each) = {high*40} min")
print(f"  TOTAL TIME: ~{low*10 + medium*20 + high*40} minutes")
