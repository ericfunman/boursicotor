#!/usr/bin/env python3
"""
Script pour vérifier le statut des GitHub Actions
"""
import time
import requests
from datetime import datetime

def check_ci_status():
    """Vérifie le statut du CI/CD"""
    url = "https://api.github.com/repos/ericfunman/boursicotor/actions/runs?status=completed&limit=5"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-Request"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        runs = response.json().get("workflow_runs", [])
        
        print(f"\n{'='*70}")
        print(f"GitHub Actions CI/CD Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        if not runs:
            print("❌ Aucun run trouvé")
            return
        
        # Affiche les 5 derniers runs
        for i, run in enumerate(runs[:5], 1):
            status = run.get("conclusion", "PENDING")
            name = run.get("name", "Unknown")
            commit = run.get("head_sha", "?")[:7]
            created = run.get("created_at", "")
            
            # Symbole selon le statut
            symbol = {
                "success": "✅",
                "failure": "❌",
                "cancelled": "⏹️",
                None: "⏳"
            }.get(status, "❓")
            
            print(f"{symbol} Run #{i} | Status: {status:12} | Commit: {commit} | {name}")
        
        # Affiche le dernier run en détail
        latest = runs[0]
        print(f"\n{'─'*70}")
        print("DERNIER RUN (Details):")
        print(f"{'─'*70}")
        print(f"Status: {latest.get('conclusion', 'PENDING')}")
        print(f"Commit: {latest.get('head_sha', 'Unknown')}")
        print(f"Message: {latest.get('name', 'Unknown')}")
        print(f"URL: https://github.com/ericfunman/boursicotor/actions/runs/{latest.get('id')}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_ci_status()
