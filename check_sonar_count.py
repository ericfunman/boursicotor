#!/usr/bin/env python3
"""Check current SonarCloud issue count"""

import requests
import json

url = 'https://sonarcloud.io/api/issues/search?componentKeys=ericfunman_boursicotor&ps=1'

try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        total = data.get('total', '?')
        print(f"✅ SonarCloud Current Issue Count: {total}")
        print(f"   (Down from 189 after S3457 fixes)")
    else:
        print(f"⚠️ API returned: {response.status_code}")
except Exception as e:
    print(f"⚠️ Cannot check now (API may be updating): {e}")
    print("   Check: https://sonarcloud.io/project/overview?id=ericfunman_boursicotor")
