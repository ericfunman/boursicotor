#!/usr/bin/env python3
"""
FIXED AUTO LOOP - Boucle d'automatisation pour atteindre 60% coverage + 0 Sonar errors
Version 2: Avec tests robustes qui passent et commits persistants
"""
import subprocess
import time
import requests
import json
import sys
import re
from datetime import datetime

class AutoLoopFixed:
    def __init__(self):
        self.coverage_target = 60
        self.sonar_target = 0
        self.max_iterations = 100
        self.iteration = 0
        self.component_key = "ericfunman_boursicotor"
        self.sonar_url = "https://sonarcloud.io/api/issues/search"
        
    def log(self, msg):
        """Log avec timestamp"""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")
        
    def run_command(self, cmd):
        """Exécuter commande shell"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", 1
    
    def pytest_coverage(self):
        """Lancer pytest et récupérer la couverture"""
        self.log("📊 Vérification couverture...")
        
        # Lancer pytest avec les deux fichiers importants
        cmd = (
            "python -m pytest tests/test_coverage_boost.py tests/test_security.py "
            "--cov=backend --cov=frontend --cov-report=term-missing -q 2>&1"
        )
        
        stdout, stderr, rc = self.run_command(cmd)
        output = stdout + stderr
        
        # Parser la couverture - chercher "TOTAL ... X%"
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if match:
            cov = int(match.group(1))
            self.log(f"   Couverture: {cov}%")
            return cov
        else:
            self.log(f"   ⚠️ Impossible de parser la couverture")
            return 0
    
    def sonar_issues(self):
        """Requête Sonar pour nombre d'issues"""
        self.log("🔴 Vérification Sonar...")
        try:
            params = {
                "componentKeys": self.component_key,
                "types": "CODE_SMELL,BUG,VULNERABILITY",
                "ps": 1  # Juste compter, pas lister
            }
            resp = requests.get(self.sonar_url, params=params, timeout=10)
            data = resp.json()
            total = data.get('total', 0)
            self.log(f"   Issues: {total}")
            
            # Parser les types principaux
            facets = data.get('facets', [])
            for facet in facets:
                if facet.get('property') == 'ruleKey':
                    for value in facet.get('values', [])[:5]:
                        rule = value.get('val', '').split(':')[-1]
                        count = value.get('count', 0)
                        self.log(f"   - {rule}: {count}")
            
            return total
        except Exception as e:
            self.log(f"   ⚠️ Erreur Sonar: {e}")
            return 999  # Très haut si erreur
    
    def run_iteration(self):
        """Une itération complète"""
        self.iteration += 1
        
        self.log(f"\n{'='*80}")
        self.log(f"🔄 ITÉRATION {self.iteration}")
        self.log(f"{'='*80}")
        
        # Mesurer couverture et Sonar avant
        coverage = self.pytest_coverage()
        sonar = self.sonar_issues()
        
        # Vérifier si objectifs atteints
        if coverage >= self.coverage_target and sonar <= self.sonar_target:
            return coverage, sonar
        
        return coverage, sonar
    
    def auto_loop(self):
        """Boucle principale - vérifie et attend"""
        self.log("\n🚀🚀🚀 AUTO LOOP LANCÉE (VERSION 2) 🚀🚀🚀")
        self.log(f"Objectif: Couverture >= {self.coverage_target}% + Sonar = 0 issues")
        self.log(f"Vérification toutes les 30 secondes")
        self.log(f"Max {self.max_iterations} itérations")
        
        for i in range(self.max_iterations):
            coverage, sonar_issues = self.run_iteration()
            
            # Vérifier si objectifs atteints
            if coverage >= self.coverage_target and sonar_issues <= self.sonar_target:
                self.log(f"\n{'='*80}")
                self.log(f"🎉🎉🎉 OBJECTIFS ATTEINTS! 🎉🎉🎉")
                self.log(f"✅ Couverture: {coverage}% >= {self.coverage_target}%")
                self.log(f"✅ Sonar: {sonar_issues} issues <= {self.sonar_target}")
                self.log(f"{'='*80}\n")
                return True
            
            # Afficher progression
            self.log(f"\n📈 Progression: Couverture {coverage}/{self.coverage_target}% | Sonar {sonar_issues} issues")
            
            # Pause avant prochaine itération (30 secondes)
            if i < self.max_iterations - 1:
                self.log(f"⏸️  Prochaine vérification dans 30s...")
                time.sleep(30)
        
        # Max iterations reached
        self.log(f"\n{'='*80}")
        self.log(f"⚠️ Max iterations ({self.max_iterations}) atteint")
        self.log(f"Couverture finale: {coverage}% / {self.coverage_target}%")
        self.log(f"Sonar final: {sonar_issues} issues / {self.sonar_target}")
        self.log(f"{'='*80}\n")
        return False


if __name__ == '__main__':
    fixer = AutoLoopFixed()
    success = fixer.auto_loop()
    sys.exit(0 if success else 1)
