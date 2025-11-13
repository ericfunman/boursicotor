#!/usr/bin/env python3
"""
Auto-fix 45 SonarCloud issues
Priority:
1. S5914 (14) - Boolean conditions in tests
2. S1192 (9) - Duplicated strings
3. S117 (14) - Parameter names (IBKR - skip camelCase due to API)
4. S1481 (1) - Unused variables
"""
import json
import re
from pathlib import Path
from typing import Dict, List

# Load issues
with open("sonar_45_issues.json") as f:
    data = json.load(f)

issues = data["issues"]

print("=" * 80)
print("🔧 AUTO-FIXING 45 SONARCLOUD ISSUES")
print("=" * 80)

# Group by rule
by_rule = {}
for issue in issues:
    rule = issue.get("rule", "UNKNOWN")
    if rule not in by_rule:
        by_rule[rule] = []
    by_rule[rule].append(issue)

fixes_count = 0

# 1. FIX S5914 - Boolean conditions (test files only)
print(f"\n1️⃣ Fixing S5914 - Boolean conditions ({len(by_rule.get('python:S5914', []))} issues)")
print("-" * 80)

for issue in by_rule.get('python:S5914', []):
    component = issue.get("component", "").replace("ericfunman_boursicotor:", "")
    line_num = issue.get("line", 0)
    message = issue.get("message", "")
    
    # Only fix test files
    if not component.startswith("tests/"):
        continue
    
    file_path = Path(component)
    if not file_path.exists():
        print(f"  ⚠️  File not found: {component}")
        continue
    
    # Read file
    with open(file_path) as f:
        content = f.read()
        lines = content.split("\n")
    
    if line_num <= 0 or line_num > len(lines):
        print(f"  ⚠️  Invalid line {line_num} in {component}")
        continue
    
    target_line = lines[line_num - 1]
    print(f"  Line {line_num}: {target_line.strip()[:60]}")
    
    # Common patterns to fix
    # "assert x == True" -> "assert x"
    # "if x == True:" -> "if x:"
    # "if x == False:" -> "if not x:"
    
    original = target_line
    
    # Replace patterns
    new_line = target_line
    new_line = re.sub(r'\s+==\s+True\b', '', new_line)
    new_line = re.sub(r'\s+==\s+False\b', '', new_line)
    new_line = re.sub(r'\bis\s+True\b', '', new_line)
    new_line = re.sub(r'\bis\s+False\b', '', new_line)
    
    if new_line != original:
        lines[line_num - 1] = new_line
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        print(f"  ✅ Fixed: {new_line.strip()[:60]}")
        fixes_count += 1
    else:
        print(f"  ⏭️  Skipped (pattern not matched)")

# 2. FIX S1481 - Unused variables
print(f"\n2️⃣ Fixing S1481 - Unused variables ({len(by_rule.get('python:S1481', []))} issues)")
print("-" * 80)

for issue in by_rule.get('python:S1481', []):
    component = issue.get("component", "").replace("ericfunman_boursicotor:", "")
    line_num = issue.get("line", 0)
    message = issue.get("message", "")
    
    file_path = Path(component)
    if not file_path.exists():
        print(f"  ⚠️  File not found: {component}")
        continue
    
    # Extract variable name from message
    match = re.search(r'"(\w+)"', message)
    if not match:
        print(f"  ⚠️  Could not extract variable name from: {message}")
        continue
    
    var_name = match.group(1)
    
    with open(file_path) as f:
        content = f.read()
        lines = content.split("\n")
    
    if line_num <= 0 or line_num > len(lines):
        print(f"  ⚠️  Invalid line {line_num}")
        continue
    
    target_line = lines[line_num - 1]
    print(f"  Line {line_num}: Replace '{var_name}' with '_'")
    
    # Replace variable name with _
    new_line = re.sub(r'\b' + var_name + r'\b', '_', target_line, count=1)
    
    if new_line != target_line:
        lines[line_num - 1] = new_line
        with open(file_path, "w") as f:
            f.write("\n".join(lines))
        print(f"  ✅ Fixed: {new_line.strip()[:60]}")
        fixes_count += 1
    else:
        print(f"  ⏭️  Could not replace")

# 3. FIX S1192 - Duplicated strings
print(f"\n3️⃣ Fixing S1192 - Duplicated strings ({len(by_rule.get('python:S1192', []))} issues)")
print("-" * 80)

s1192_issues = by_rule.get('python:S1192', [])
files_with_s1192 = {}

for issue in s1192_issues:
    component = issue.get("component", "").replace("ericfunman_boursicotor:", "")
    if component not in files_with_s1192:
        files_with_s1192[component] = []
    files_with_s1192[component].append(issue)

print(f"  Found duplicated strings in {len(files_with_s1192)} files:")
for file_path in sorted(files_with_s1192.keys()):
    count = len(files_with_s1192[file_path])
    print(f"    - {file_path}: {count} duplicates")
    print(f"      (Manual fix recommended: extract to constants)")

# 4. S117 - Parameter names (skip - IBKR API compatibility)
print(f"\n4️⃣ Skipping S117 - Parameter names ({len(by_rule.get('python:S117', []))} issues)")
print("-" * 80)
print(f"  ⚠️  IBKR connector uses camelCase due to Interactive Brokers API")
print(f"  Action: Add # noqa: S117 comment to function signatures")

print("\n" + "=" * 80)
print(f"✅ FIXED: {fixes_count} issues")
print(f"⏭️  SKIPPED: {len(by_rule.get('python:S117', []))} (IBKR API compatibility)")
print(f"📋 TODO: {len(by_rule.get('python:S1192', []))} (Extract strings to constants)")
print("=" * 80)
