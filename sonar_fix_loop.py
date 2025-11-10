#!/usr/bin/env python3
"""
SonarCloud Issues Fixer - Boucle Interactive
Récupère les 586 issues et propose une boucle de correction par sévérité et type.

Usage:
    python sonar_fix_loop.py                   # Mode interactif
    python sonar_fix_loop.py --auto            # Mode automatique
    python sonar_fix_loop.py --report          # Générer rapport
    python sonar_fix_loop.py --by-file         # Analyser par fichier
"""

import requests
import json
import sys
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SONAR_HOST = "https://sonarcloud.io"
SONAR_PROJECT_KEY = "ericfunman_boursicotor"
SONAR_ORGANIZATION = "ericfunman"


class SonarIssuesAnalyzer:
    """Analyse les issues SonarCloud et propose des corrections"""

    def __init__(self):
        self.host = SONAR_HOST
        self.project_key = SONAR_PROJECT_KEY
        self.organization = SONAR_ORGANIZATION
        self.session = requests.Session()
        self.all_issues = []
        self.issues_by_type = defaultdict(list)
        self.issues_by_severity = defaultdict(list)
        self.issues_by_file = defaultdict(list)

    def fetch_all_issues(self) -> List[Dict]:
        """Récupère TOUTES les 586 issues via pagination"""
        print(f"🔍 Récupération de TOUTES les issues SonarCloud...")
        print(f"   Endpoint: {self.host}/api/issues/search")
        print(f"   Project: {self.project_key}")
        print()

        all_issues = []
        page = 1
        page_size = 500  # Max autorisé

        while True:
            params = {
                "componentKeys": self.project_key,
                "organization": self.organization,
                "p": page,
                "ps": page_size,
                "s": "SEVERITY",  # Trier par sévérité (du plus grave au moins grave)
            }

            try:
                url = f"{self.host}/api/issues/search"
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                result = response.json()

                issues = result.get("issues", [])
                total = result.get("total", 0)
                paging = result.get("paging", {})

                if not issues:
                    print(f"✅ Fin de pagination atteinte")
                    break

                all_issues.extend(issues)
                print(
                    f"  📄 Page {page}/{paging.get('pageIndex', 1)}: "
                    f"{len(issues)} issues | "
                    f"Cumul: {len(all_issues)}/{total}"
                )

                # Pause pour ne pas surcharger l'API
                time.sleep(0.5)

                # Vérifier si c'est la dernière page
                if paging.get("pageIndex") >= (paging.get("pages") or 1):
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur API: {e}")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
                break

        self.all_issues = all_issues
        print(f"\n✅ Total des issues récupérées: {len(all_issues)}\n")
        return all_issues

    def categorize_issues(self):
        """Catégorise les issues par type et sévérité"""
        print("📊 Catégorisation des issues...")

        for issue in self.all_issues:
            issue_type = issue.get("type", "UNKNOWN")
            severity = issue.get("severity", "UNKNOWN")
            file_path = issue.get("component", "").split(":")[-1]

            self.issues_by_type[issue_type].append(issue)
            self.issues_by_severity[severity].append(issue)
            self.issues_by_file[file_path].append(issue)

    def print_analysis(self):
        """Affiche une analyse détaillée des issues"""
        print("\n" + "=" * 80)
        print("📋 ANALYSE DES ISSUES SONARCLOUD")
        print("=" * 80)

        # Par sévérité
        print("\n🔴 RÉPARTITION PAR SÉVÉRITÉ:")
        severity_order = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
        for severity in severity_order:
            count = len(self.issues_by_severity[severity])
            if count > 0:
                emoji = "🔴" if severity == "BLOCKER" else "🟠" if severity == "CRITICAL" else "🟡" if severity == "MAJOR" else "🟢" if severity == "MINOR" else "⚪"
                print(f"  {emoji} {severity:10s}: {count:3d} issues ({count * 100 // len(self.all_issues):3d}%)")

        # Par type
        print("\n📝 RÉPARTITION PAR TYPE:")
        for issue_type in sorted(self.issues_by_type.keys()):
            count = len(self.issues_by_type[issue_type])
            emoji = "🐛" if issue_type == "BUG" else "👃" if issue_type == "CODE_SMELL" else "🔒" if issue_type == "VULNERABILITY" else "ℹ️"
            print(f"  {emoji} {issue_type:20s}: {count:3d} issues ({count * 100 // len(self.all_issues):3d}%)")

        # Top 10 des fichiers les plus problématiques
        print("\n📁 TOP 10 DES FICHIERS LES PLUS PROBLÉMATIQUES:")
        sorted_files = sorted(self.issues_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for i, (file_path, issues) in enumerate(sorted_files, 1):
            print(f"  {i:2d}. {file_path:50s}: {len(issues):3d} issues")

    def print_top_issues(self, limit: int = 20):
        """Affiche les top issues par sévérité"""
        print("\n" + "=" * 80)
        print(f"🎯 TOP {limit} DES ISSUES LES PLUS CRITIQUES")
        print("=" * 80)

        # Filtrer par sévérité (BLOCKER puis CRITICAL)
        critical_issues = [
            i for i in self.all_issues
            if i.get("severity") in ["BLOCKER", "CRITICAL"]
        ][:limit]

        for idx, issue in enumerate(critical_issues, 1):
            severity = issue.get("severity", "?")
            issue_type = issue.get("type", "?")
            message = issue.get("message", "N/A")[:60]
            file_path = issue.get("component", "?").split(":")[-1]
            line = issue.get("line", "?")

            emoji_severity = "🔴" if severity == "BLOCKER" else "🟠"
            emoji_type = "🐛" if issue_type == "BUG" else "👃" if issue_type == "CODE_SMELL" else "🔒"

            print(f"\n  {idx:2d}. {emoji_severity} {emoji_type} {severity}")
            print(f"      Type: {issue_type}")
            print(f"      File: {file_path}:{line}")
            print(f"      Rule: {issue.get('rule', 'N/A')}")
            print(f"      Msg:  {message}...")

    def export_json(self, filename: str = "sonar_issues.json"):
        """Exporte les issues en JSON"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "project": self.project_key,
            "total_issues": len(self.all_issues),
            "by_severity": {
                severity: len(issues)
                for severity, issues in self.issues_by_severity.items()
            },
            "by_type": {
                issue_type: len(issues)
                for issue_type, issues in self.issues_by_type.items()
            },
            "issues": self.all_issues,
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"✅ Exporté vers: {filename}")

    def export_csv_summary(self, filename: str = "sonar_issues_summary.csv"):
        """Exporte un résumé en CSV"""
        import csv

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Index",
                    "Severity",
                    "Type",
                    "Rule",
                    "Message",
                    "File",
                    "Line",
                    "Status",
                ]
            )

            for idx, issue in enumerate(self.all_issues, 1):
                writer.writerow(
                    [
                        idx,
                        issue.get("severity", "?"),
                        issue.get("type", "?"),
                        issue.get("rule", "?"),
                        issue.get("message", "?")[:100],
                        issue.get("component", "?").split(":")[-1],
                        issue.get("line", "?"),
                        issue.get("status", "?"),
                    ]
                )

        print(f"✅ CSV exporté vers: {filename}")

    def interactive_loop(self):
        """Boucle interactive pour naviguer et corriger les issues"""
        print("\n" + "=" * 80)
        print("🔄 MODE INTERACTIF - BOUCLE DE CORRECTION")
        print("=" * 80)

        severity_order = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]

        for severity in severity_order:
            issues = self.issues_by_severity[severity]
            if not issues:
                continue

            print(f"\n{'='*80}")
            print(f"🔍 Traitement des {len(issues)} issues {severity}")
            print(f"{'='*80}")

            for idx, issue in enumerate(issues[:10], 1):  # Limiter à 10 par sévérité
                print(f"\n  [{idx}/{min(10, len(issues))}] {severity}")
                print(f"  Type: {issue.get('type')}")
                print(f"  Rule: {issue.get('rule')}")
                print(f"  File: {issue.get('component', '?').split(':')[-1]}:{issue.get('line', '?')}")
                print(f"  Msg:  {issue.get('message', '?')}")
                print(f"  Status: {issue.get('status', '?')}")

                # Proposer action
                print(f"\n  Actions:")
                print(f"    [f] Fix this issue")
                print(f"    [s] Skip to next")
                print(f"    [q] Quit")

                choice = input("  Choice: ").lower().strip()

                if choice == "q":
                    print("\n✅ Fin de la boucle interactive")
                    return
                elif choice == "f":
                    print(f"  💡 Suggestion: Créer une issue GitHub pour cette correction")
                    print(f"     https://github.com/ericfunman/boursicotor/issues/new")
                elif choice == "s":
                    continue

            # Pause entre les sévérités
            if severity != severity_order[-1]:
                input(f"\n  Appuyez sur ENTER pour passer à {severity_order[severity_order.index(severity) + 1]}...")


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(description="Analyse et corrige les issues SonarCloud")
    parser.add_argument("--auto", action="store_true", help="Mode automatique (pas d'interaction)")
    parser.add_argument("--report", action="store_true", help="Générer rapport et exporter")
    parser.add_argument("--by-file", action="store_true", help="Analyser par fichier")
    parser.add_argument("--json", action="store_true", help="Exporter en JSON")
    parser.add_argument("--csv", action="store_true", help="Exporter en CSV")

    args = parser.parse_args()

    # Créer analyseur
    analyzer = SonarIssuesAnalyzer()

    # Récupérer les issues
    print("🚀 Démarrage du SonarCloud Issues Fixer\n")
    issues = analyzer.fetch_all_issues()

    if not issues:
        print("❌ Aucune issue trouvée")
        return 1

    # Catégoriser
    analyzer.categorize_issues()

    # Afficher analyse
    analyzer.print_analysis()
    analyzer.print_top_issues(limit=20)

    # Exports
    if args.report or args.json:
        analyzer.export_json()

    if args.report or args.csv:
        analyzer.export_csv_summary()

    # Boucle interactive
    if not args.auto:
        analyzer.interactive_loop()

    print("\n✅ Analyse complète!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
