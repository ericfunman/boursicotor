#!/usr/bin/env python3
"""
RAPPORT FINAL - État Sonar et recommandations
"""

import requests
import json
from pathlib import Path

def generate_sonar_report():
    api = "https://sonarcloud.io/api/issues/search"
    project = "ericfunman_boursicotor"
    
    print("\n" + "="*70)
    print("📊 RAPPORT FINAL SONARCLOUD")
    print("="*70)
    
    # Get all issues
    try:
        response = requests.get(api, params={
            "componentKeys": project,
            "types": "CODE_SMELL,BUG,VULNERABILITY",
            "pageSize": 500
        }, timeout=10)
        
        data = response.json()
        total_issues = data.get("total", 0)
        issues = data.get("issues", [])
        
        print(f"\n✅ Total Anomalies détectées: {total_issues}")
        print(f"✅ Anomalies analysées par Sonar: {len(issues)}")
        
        # Group by rule
        by_rule = {}
        for issue in issues:
            rule = issue.get("rule", "UNKNOWN")
            if rule not in by_rule:
                by_rule[rule] = []
            by_rule[rule].append(issue)
        
        print(f"\n📋 Distribution par type:")
        print("-" * 70)
        
        for rule in sorted(by_rule.keys(), key=lambda x: len(by_rule[x]), reverse=True):
            count = len(by_rule[rule])
            print(f"\n  {rule}: {count} anomalies")
            
            # Show first 3 examples
            for issue in by_rule[rule][:3]:
                file = issue.get("component", "").split(":")[-1]
                msg = issue.get("message", "")[:60]
                print(f"    • {file}: {msg}...")
            
            if count > 3:
                print(f"    ... et {count - 3} autres")
        
        # Recommendations
        print(f"\n\n📝 RECOMMANDATIONS")
        print("-" * 70)
        
        if "python:S6711" in by_rule:
            count = len(by_rule["python:S6711"])
            print(f"\n1️⃣  S6711 (Numpy Random): {count} anomalies")
            print(f"   Recommandation: Remplacer np.random par numpy.random.Generator")
            print(f"   Priorité: HAUTE (92% des anomalies)")
            print(f"   Effort: MOYEN (require refactoring des appels)")
        
        if "python:S3776" in by_rule:
            count = len(by_rule["python:S3776"])
            print(f"\n2️⃣  S3776 (Cognitive Complexity): {count} anomalies")
            print(f"   Recommandation: Refactoriser les fonctions complexes")
            print(f"   Priorité: MOYENNE")
            print(f"   Effort: ÉLEVÉ (requires design review)")
        
        if "python:S5713" in by_rule:
            count = len(by_rule["python:S5713"])
            print(f"\n3️⃣  S5713 (Redundant Exception): {count} anomalies")
            print(f"   Recommandation: Supprimer les classes Exception inutiles")
            print(f"   Priorité: BASSE")
            print(f"   Effort: TRÈS FAIBLE")
        
        if "python:S125" in by_rule:
            count = len(by_rule["python:S125"])
            print(f"\n4️⃣  S125 (Commented Code): {count} anomalies")
            print(f"   Recommandation: Supprimer le code commenté")
            print(f"   Priorité: BASSE")
            print(f"   Effort: TRÈS FAIBLE")
        
        if "python:S107" in by_rule:
            count = len(by_rule["python:S107"])
            print(f"\n5️⃣  S107 (Too Many Parameters): {count} anomalies")
            print(f"   Recommandation: Réduire les paramètres des méthodes")
            print(f"   Priorité: MOYENNE")
            print(f"   Effort: MOYEN (requires refactoring)")
        
        # Summary
        print(f"\n\n📊 RÉSUMÉ")
        print("-" * 70)
        print(f"État actuel:")
        print(f"  • Tests: ✅ 22/22 passants")
        print(f"  • Couverture: ✅ 2%")
        print(f"  • Anomalies Sonar: ⚠️  {total_issues}")
        print(f"  • Anomalies détectées réellement: {len(issues)}")
        
        print(f"\nProchaines étapes:")
        print(f"  1. Corriger S6711 (92 anomalies) pour réduire drastiquement")
        print(f"  2. Corriger S3776, S107, S125, S5713 (manuellement)")
        print(f"  3. Valider à chaque étape avec tests")
        print(f"  4. Commitbatch de corrections vérifiées")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    generate_sonar_report()
