#!/usr/bin/env python3
"""
Récupère et analyse les anomalies Sonar actuelles
"""

import requests
import json
from collections import defaultdict

def get_sonar_issues():
    """Récupère toutes les anomalies Sonar"""
    api_url = "https://sonarcloud.io/api/issues/search"
    
    issues_by_type = defaultdict(int)
    all_issues = []
    
    page = 1
    page_size = 500
    
    try:
        while True:
            params = {
                "componentKeys": "ericfunman_boursicotor",
                "types": "CODE_SMELL,BUG,VULNERABILITY",
                "pageSize": page_size,
                "p": page
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            data = response.json()
            
            issues = data.get("issues", [])
            if not issues:
                break
            
            for issue in issues:
                rule = issue.get("rule", "UNKNOWN")
                issues_by_type[rule] += 1
                all_issues.append({
                    "rule": rule,
                    "message": issue.get("message", ""),
                    "file": issue.get("component", "").split(":")[-1] if ":" in issue.get("component", "") else issue.get("component", "")
                })
            
            if len(issues) < page_size:
                break
            
            page += 1
        
        print(f"Total: {len(all_issues)} anomalies\n")
        print("Par type de règle:")
        for rule, count in sorted(issues_by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"  {rule}: {count}")
        
        print("\nTop 20 anomalies:")
        rule_counts = defaultdict(int)
        for issue in all_issues[:20]:
            rule = issue["rule"]
            print(f"  {rule} - {issue['file']}: {issue['message'][:60]}")
            
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    get_sonar_issues()
