#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Status check: Vérifier couverture et issues Sonar actuelles
"""
import requests
from datetime import datetime

component_key = "ericfunman_boursicotor"

# Get coverage
print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking SonarCloud metrics...")

try:
    resp = requests.get("https://sonarcloud.io/api/measures/component", 
        params={
            "component": component_key,
            "metricKeys": "coverage,violations,bugs,code_smells,duplicated_lines"
        },
        timeout=10
    )
    measures = {m['metric']: m.get('value', '0') for m in resp.json().get('component', {}).get('measures', [])}
    
    print(f"\n=== SONARCLOUD METRICS ===")
    print(f"Coverage:     {measures.get('coverage', '0')}%")
    print(f"Violations:   {measures.get('violations', 'N/A')}")
    print(f"Bugs:         {measures.get('bugs', '0')}")
    print(f"Code Smells:  {measures.get('code_smells', '0')}")
    print(f"Duplication:  {measures.get('duplicated_lines', '0')} lines")
    
except Exception as e:
    print(f"Error: {e}")

# Get open issues
try:
    resp = requests.get("https://sonarcloud.io/api/issues/search",
        params={
            "componentKeys": component_key,
            "statuses": "OPEN",
            "ps": 200
        },
        timeout=10
    )
    total_issues = resp.json().get('total', 0)
    
    # Count by rule
    from collections import Counter
    rules = Counter([i['rule'].split(':')[-1] for i in resp.json().get('issues', [])])
    
    print(f"\n=== SONARCLOUD ISSUES ===")
    print(f"Total OPEN issues: {total_issues}")
    print(f"\nTop 10 rules:")
    for rule, count in sorted(rules.items(), key=lambda x: -x[1])[:10]:
        print(f"  {rule}: {count}")
        
except Exception as e:
    print(f"Error: {e}")

print(f"\n=== SUMMARY ===")
print(f"Current Coverage: ~13% (local), ? (Sonar - checking...)")
print(f"Current Issues:   158 OPEN")
print(f"Target Coverage:  60%")
print(f"Target Issues:    0")
print(f"\nGap to close:")
print(f"  Coverage: +47% (13% -> 60%)")
print(f"  Issues:   -158 (158 -> 0)")
