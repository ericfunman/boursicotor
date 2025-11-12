#!/usr/bin/env python3
"""
Analyze remaining SonarCloud issues
"""

import json
import requests
from pathlib import Path
from collections import Counter

# Try to fetch from API
try:
    url = 'https://sonarcloud.io/api/issues/search?componentKeys=ericfunman_boursicotor&ps=500'
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        issues = data.get('issues', [])
        
        # Count by rule
        rules = Counter()
        files = Counter()
        
        for issue in issues:
            rule = issue.get('rule', 'unknown')
            component = issue.get('component', 'unknown')
            component_name = component.split(':')[-1] if ':' in component else component
            
            rules[rule] += 1
            files[component_name] += 1
        
        print(f"\n📊 SONARCLOUD CURRENT STATUS: {len(issues)} issues\n")
        print("=" * 70)
        print("TOP ISSUES BY RULE")
        print("=" * 70)
        
        for rule, count in rules.most_common(15):
            print(f"{rule:30} : {count:3} issues")
        
        print("\n" + "=" * 70)
        print("TOP FILES BY ISSUE COUNT")
        print("=" * 70)
        
        for file, count in files.most_common(10):
            print(f"{file:40} : {count:3} issues")
            
except Exception as e:
    print(f"⚠️ Cannot fetch: {e}")
    print("\nCheck dashboard: https://sonarcloud.io/project/overview?id=ericfunman_boursicotor")
