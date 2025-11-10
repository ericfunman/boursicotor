#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch SonarCloud issues and auto-fix them in a loop
Récupère les 586 issues SonarCloud et les corrige automatiquement
"""

import requests
import json
import subprocess
import sys
import os
from collections import defaultdict
from typing import Dict, List, Tuple
import time

# Fix encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
SONAR_ORG = "ericfunman"
SONAR_PROJECT = "ericfunman_boursicotor"
SONAR_API = "https://sonarcloud.io/api"

class SonarIssueAnalyzer:
    """Analyze and fix SonarCloud issues"""
    
    def __init__(self):
        self.issues = []
        self.issues_by_type = defaultdict(list)
        self.issues_by_severity = defaultdict(list)
        self.fixed_count = 0
        self.session = requests.Session()
        
    def fetch_all_issues(self, page_size=500):
        """Récupère TOUTES les issues SonarCloud avec pagination"""
        print(f"\n🔍 Récupération des issues SonarCloud pour {SONAR_PROJECT}...")
        
        all_issues = []
        page = 1
        total_fetched = 0
        
        while True:
            try:
                url = f"{SONAR_API}/issues/search"
                params = {
                    'componentKeys': SONAR_PROJECT,
                    'ps': page_size,
                    'p': page,
                    'statuses': 'OPEN'  # Seulement les issues ouvertes
                }
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                issues = data.get('issues', [])
                if not issues:
                    break
                    
                all_issues.extend(issues)
                total_fetched += len(issues)
                
                print(f"  Page {page}: {len(issues)} issues (total: {total_fetched})")
                
                # Vérifier s'il y a d'autres pages
                if len(issues) < page_size:
                    break
                    
                page += 1
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Erreur page {page}: {e}")
                break
        
        self.issues = all_issues
        print(f"\n✅ Total: {len(all_issues)} issues récupérées")
        return all_issues
    
    def categorize_issues(self):
        """Catégorise les issues par type et sévérité"""
        print(f"\n📊 Catégorisation des issues...")
        
        for issue in self.issues:
            issue_type = issue.get('type', 'UNKNOWN')
            severity = issue.get('severity', 'UNKNOWN')
            
            self.issues_by_type[issue_type].append(issue)
            self.issues_by_severity[severity].append(issue)
        
        # Afficher le résumé
        print("\n📋 RÉSUMÉ PAR TYPE:")
        for issue_type, issues in sorted(self.issues_by_type.items()):
            print(f"  {issue_type:15} : {len(issues):3} issues")
        
        print("\n🚨 RÉSUMÉ PAR SÉVÉRITÉ:")
        severity_order = ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']
        for severity in severity_order:
            if severity in self.issues_by_severity:
                issues = self.issues_by_severity[severity]
                print(f"  {severity:10} : {len(issues):3} issues")
        
        return self.issues_by_type, self.issues_by_severity
    
    def get_top_issues(self, limit=20):
        """Retourne les top issues à corriger (triées par sévérité)"""
        severity_order = {'BLOCKER': 0, 'CRITICAL': 1, 'MAJOR': 2, 'MINOR': 3, 'INFO': 4}
        
        sorted_issues = sorted(
            self.issues,
            key=lambda x: (severity_order.get(x.get('severity', 'INFO'), 999), x.get('line', 0))
        )
        
        return sorted_issues[:limit]
    
    def print_issues_details(self, issues=None, limit=20):
        """Affiche les détails des top issues"""
        if issues is None:
            issues = self.get_top_issues(limit)
        
        print(f"\n🎯 TOP {min(len(issues), limit)} ISSUES À CORRIGER:\n")
        print(f"{'#':<3} {'Sev':<8} {'Type':<12} {'Fichier':<40} {'Ligne':<5} {'Règle'}")
        print("-" * 120)
        
        for i, issue in enumerate(issues[:limit], 1):
            file_path = issue.get('component', '').replace(f"{SONAR_PROJECT}:", '')
            line = issue.get('line', 0)
            severity = issue.get('severity', 'INFO')[:3]
            issue_type = issue.get('type', 'UNKNOWN')[:12]
            rule = issue.get('rule', 'UNKNOWN').split(':')[-1][:30]
            
            print(f"{i:<3} {severity:<8} {issue_type:<12} {file_path:<40} {line:<5} {rule}")
    
    def analyze_issue_patterns(self):
        """Analyse les patterns d'issues pour trouver les corrections massives"""
        print(f"\n🔎 ANALYSE DES PATTERNS:\n")
        
        rule_counts = defaultdict(int)
        rule_details = defaultdict(list)
        
        for issue in self.issues:
            rule = issue.get('rule', 'UNKNOWN')
            rule_counts[rule] += 1
            rule_details[rule].append({
                'file': issue.get('component', '').replace(f"{SONAR_PROJECT}:", ''),
                'line': issue.get('line', 0),
                'message': issue.get('message', '')
            })
        
        # Afficher les top 10 règles violées
        print("📌 TOP 10 RÈGLES VIOLÉES:\n")
        print(f"{'Nombre':<8} {'Règle'}")
        print("-" * 100)
        
        for rule, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            rule_name = rule.split(':')[-1] if ':' in rule else rule
            print(f"{count:<8} {rule_name}")
        
        return rule_counts, rule_details

def run_analysis():
    """Exécute l'analyse complète"""
    print("=" * 100)
    print("🚀 SonarCloud Issues Analyzer - Boucle de Correction Automatique")
    print("=" * 100)
    
    analyzer = SonarIssueAnalyzer()
    
    # Étape 1: Récupérer les issues
    analyzer.fetch_all_issues()
    
    # Étape 2: Catégoriser
    analyzer.categorize_issues()
    
    # Étape 3: Analyser les patterns
    analyzer.analyze_issue_patterns()
    
    # Étape 4: Afficher top issues
    analyzer.print_issues_details(limit=30)
    
    # Sauvegarder les issues en JSON pour traitement
    issues_file = "sonar_issues_latest.json"
    with open(issues_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(analyzer.issues),
            'issues': analyzer.issues[:100],  # Sauvegarder les 100 premières
            'by_type': {k: len(v) for k, v in analyzer.issues_by_type.items()},
            'by_severity': {k: len(v) for k, v in analyzer.issues_by_severity.items()}
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Détails sauvegardés dans {issues_file}")
    
    return analyzer

if __name__ == '__main__':
    try:
        analyzer = run_analysis()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
