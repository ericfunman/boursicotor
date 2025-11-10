#!/usr/bin/env python3
"""Find S125 issues"""

import requests

api = "https://sonarcloud.io/api/issues/search"
r = requests.get(api, params={
    "componentKeys": "ericfunman_boursicotor",
    "rules": "python:S125",
    "pageSize": 100
}, timeout=10)

data = r.json()
print(f"Found {len(data.get('issues', []))} S125 issues:\n")

for issue in data.get("issues", []):
    component = issue.get("component", "")
    file = component.split(":")[-1] if ":" in component else component
    print(f"File: {file}")
    print(f"  Line: {issue.get('line')}")
    print(f"  Message: {issue.get('message')}")
    print()
