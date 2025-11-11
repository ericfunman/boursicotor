#!/usr/bin/env python3
"""
Find remaining S3457 (empty f-strings) issues
"""

import requests
import json

url = 'https://sonarcloud.io/api/issues/search?componentKeys=ericfunman_boursicotor&rules=python:S3457&ps=100'

try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        issues = data.get('issues', [])
        
        print(f"\n📌 Remaining S3457 Issues: {len(issues)}\n")
        
        for i, issue in enumerate(issues[:20], 1):
            component = issue.get('component', '').split(':')[-1]
            line = issue.get('line', '?')
            message = issue.get('message', '')
            print(f"{i:2}. {component:30} Line {line:4} - {message[:50]}")
            
except Exception as e:
    print(f"Error: {e}")
