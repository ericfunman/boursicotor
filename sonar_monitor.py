#!/usr/bin/env python3
"""
SonarCloud Monitor Script
Récupère les issues SonarCloud et la couverture de test pour boucler sur les corrections.

Usage:
    python sonar_monitor.py                  # Mode interactif
    python sonar_monitor.py --auto           # Mode automatique
    python sonar_monitor.py --json           # Export en JSON
"""

import requests
import json
import sys
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from xml.etree import ElementTree as ET
from datetime import datetime

# Configuration
SONAR_HOST = "https://sonarcloud.io"
SONAR_PROJECT_KEY = "ericfunman_boursicotor"
SONAR_ORGANIZATION = "ericfunman"

# Token (optionnel, mais permet un meilleur taux de limite)
SONAR_TOKEN = None  # À définir via variable d'environnement


class SonarMonitor:
    """Classe pour récupérer et analyser les données SonarCloud"""

    def __init__(self, host: str = SONAR_HOST, project_key: str = SONAR_PROJECT_KEY, token: Optional[str] = None):
        self.host = host
        self.project_key = project_key
        self.organization = SONAR_ORGANIZATION
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Effectue une requête à l'API SonarCloud"""
        url = f"{self.host}/api/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur API: {e}")
            return {}

    def get_issues(self, issue_type: Optional[str] = None, severity: Optional[str] = None) -> List[Dict]:
        """Récupère les issues du projet"""
        params = {
            "componentKeys": self.project_key,
            "organization": self.organization,
            "ps": 500,  # Page size
        }

        if issue_type:
            params["types"] = issue_type
        if severity:
            params["severities"] = severity

        result = self._make_request("issues/search", params)
        return result.get("issues", [])

    def get_coverage(self) -> Dict:
        """Récupère la couverture de test"""
        params = {
            "component": self.project_key,
            "organization": self.organization,
            "metricKeys": "coverage,lines_to_cover,uncovered_lines,line_coverage,conditions_to_cover,uncovered_conditions",
        }

        result = self._make_request("measures/component", params)
        measures = {}

        for measure in result.get("component", {}).get("measures", []):
            key = measure.get("metric")
            value = measure.get("value")
            measures[key] = value

        return measures

    def get_quality_metrics(self) -> Dict:
        """Récupère les métriques de qualité générale"""
        params = {
            "component": self.project_key,
            "organization": self.organization,
            "metricKeys": (
                "bugs,code_smells,duplicated_lines,sqale_index,reliability_rating,"
                "security_rating,maintainability_rating,ncloc,comment_lines_density"
            ),
        }

        result = self._make_request("measures/component", params)
        metrics = {}

        for measure in result.get("component", {}).get("measures", []):
            key = measure.get("metric")
            value = measure.get("value")
            metrics[key] = value

        return metrics

    def get_local_coverage(self) -> Optional[Dict]:
        """Récupère la couverture depuis coverage.xml local"""
        coverage_file = Path("coverage.xml")

        if not coverage_file.exists():
            return None

        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            coverage_info = {
                "lines_valid": root.get("lines-valid", "0"),
                "lines_covered": root.get("lines-covered", "0"),
                "line_rate": root.get("line-rate", "0"),
                "branches_valid": root.get("branches-valid", "0"),
                "branches_covered": root.get("branches-covered", "0"),
                "branch_rate": root.get("branch-rate", "0"),
                "timestamp": datetime.now().isoformat(),
            }

            # Calculer percentage
            lines_valid = int(coverage_info["lines_valid"])
            lines_covered = int(coverage_info["lines_covered"])
            if lines_valid > 0:
                coverage_info["coverage_percent"] = round(
                    (lines_covered / lines_valid) * 100, 2
                )

            return coverage_info
        except Exception as e:
            print(f"⚠️  Erreur lecture coverage.xml: {e}")
            return None

    def print_summary(self):
        """Affiche un résumé du projet"""
        print("\n" + "=" * 70)
        print(f"📊 SONARCLOUD PROJECT SUMMARY")
        print("=" * 70)
        print(f"Project: {self.project_key}")
        print(f"Organization: {self.organization}")
        print(f"Host: {self.host}")
        print()

        # Récupérer les données
        print("🔄 Récupération des données SonarCloud...")
        issues = self.get_issues()
        coverage = self.get_coverage()
        metrics = self.get_quality_metrics()
        local_coverage = self.get_local_coverage()

        # Afficher les issues par sévérité
        print("\n📋 ISSUES BY SEVERITY")
        print("-" * 70)

        severities = {
            "BLOCKER": (issues, "BLOCKER"),
            "CRITICAL": (issues, "CRITICAL"),
            "MAJOR": (issues, "MAJOR"),
            "MINOR": (issues, "MINOR"),
            "INFO": (issues, "INFO"),
        }

        total_issues = 0
        for sev_name, (all_issues, sev_filter) in severities.items():
            sev_issues = [i for i in all_issues if i.get("severity") == sev_filter]
            count = len(sev_issues)
            total_issues += count
            icon = "🔴" if sev_name == "BLOCKER" else (
                "🟠" if sev_name == "CRITICAL" else (
                    "🟡" if sev_name == "MAJOR" else (
                        "🔵" if sev_name == "MINOR" else "⚪"
                    )
                )
            )
            print(f"{icon} {sev_name:10s}: {count:3d} issues")

        print(f"{'─' * 70}")
        print(f"{'TOTAL':15s}: {total_issues:3d} issues")

        # Afficher les issues par type
        print("\n📌 ISSUES BY TYPE")
        print("-" * 70)

        types_dict = {}
        for issue in issues:
            issue_type = issue.get("type", "UNKNOWN")
            types_dict[issue_type] = types_dict.get(issue_type, 0) + 1

        for issue_type, count in sorted(types_dict.items(), key=lambda x: -x[1]):
            icon = "🐛" if issue_type == "BUG" else (
                "👃" if issue_type == "CODE_SMELL" else (
                    "🔒" if issue_type == "VULNERABILITY" else "?"
                )
            )
            print(f"{icon} {issue_type:15s}: {count:3d} issues")

        # Afficher les règles principales avec les plus d'issues
        print("\n🎯 TOP 10 RULES BY ISSUE COUNT")
        print("-" * 70)

        rules_dict = {}
        for issue in issues:
            rule = issue.get("rule", "UNKNOWN")
            rules_dict[rule] = rules_dict.get(rule, 0) + 1

        for i, (rule, count) in enumerate(
            sorted(rules_dict.items(), key=lambda x: -x[1])[:10], 1
        ):
            severity = next(
                (i for i in issues if i.get("rule") == rule),
                {}
            ).get("severity", "?")
            print(f"{i:2d}. {rule:50s} {count:3d} ({severity})")

        # Afficher la couverture
        print("\n📈 TEST COVERAGE")
        print("-" * 70)

        if coverage:
            print(f"Coverage (from SonarCloud): {coverage.get('coverage', 'N/A')}%")
        else:
            print("Coverage (from SonarCloud): Not available")

        if local_coverage:
            coverage_percent = local_coverage.get("coverage_percent", "N/A")
            lines_covered = local_coverage.get("lines_covered", 0)
            lines_valid = local_coverage.get("lines_valid", 0)
            print(f"Coverage (from local):      {coverage_percent}% ({lines_covered}/{lines_valid} lines)")
        else:
            print("Coverage (from local):      No coverage.xml found")

        # Afficher les métriques de qualité
        print("\n🏅 QUALITY METRICS")
        print("-" * 70)

        metrics_display = {
            "Bugs": metrics.get("bugs", "N/A"),
            "Code Smells": metrics.get("code_smells", "N/A"),
            "Duplicated Lines": metrics.get("duplicated_lines", "N/A"),
            "Lines of Code": metrics.get("ncloc", "N/A"),
            "Comment Density": metrics.get("comment_lines_density", "N/A"),
            "Reliability Rating": metrics.get("reliability_rating", "N/A"),
            "Security Rating": metrics.get("security_rating", "N/A"),
            "Maintainability Rating": metrics.get("maintainability_rating", "N/A"),
        }

        for name, value in metrics_display.items():
            print(f"{name:25s}: {value}")

        print("\n" + "=" * 70)
        return {
            "total_issues": total_issues,
            "issues": issues,
            "coverage": coverage,
            "local_coverage": local_coverage,
            "metrics": metrics,
        }

    def export_json(self, output_file: str = "sonar_report.json"):
        """Exporte le rapport en JSON"""
        issues = self.get_issues()
        coverage = self.get_coverage()
        metrics = self.get_quality_metrics()
        local_coverage = self.get_local_coverage()

        report = {
            "timestamp": datetime.now().isoformat(),
            "project": self.project_key,
            "organization": self.organization,
            "issues_count": len(issues),
            "issues": issues,
            "coverage": coverage,
            "local_coverage": local_coverage,
            "metrics": metrics,
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Rapport exporté: {output_file}")
        return report


def interactive_loop(monitor: SonarMonitor):
    """Boucle interactive de correction"""
    print("\n🔄 MODE INTERACTIF - CORRECTION DES ISSUES")
    print("=" * 70)

    while True:
        print("\nOptions:")
        print("1. Afficher les issues")
        print("2. Filtrer par sévérité (BLOCKER, CRITICAL, MAJOR)")
        print("3. Filtrer par type (BUG, CODE_SMELL, VULNERABILITY)")
        print("4. Afficher la couverture de test")
        print("5. Exporter en JSON")
        print("6. Rafraîchir les données")
        print("0. Quitter")

        choice = input("\n👉 Choix: ").strip()

        if choice == "1":
            issues = monitor.get_issues()
            print(f"\n📋 Toutes les issues ({len(issues)} total)")
            print("-" * 70)
            for i, issue in enumerate(issues[:20], 1):
                print(
                    f"{i:2d}. [{issue.get('severity'):8s}] {issue.get('message', 'N/A')[:60]}"
                )
                print(f"    Fichier: {issue.get('component', 'N/A')}")
                print(f"    Règle: {issue.get('rule', 'N/A')}")
                print()

            if len(issues) > 20:
                print(f"... et {len(issues) - 20} autres issues")

        elif choice == "2":
            severity = input("Sévérité (BLOCKER/CRITICAL/MAJOR/MINOR/INFO): ").strip().upper()
            issues = monitor.get_issues(severity=severity)
            print(f"\n📋 Issues avec sévérité {severity} ({len(issues)} total)")
            print("-" * 70)
            for i, issue in enumerate(issues[:10], 1):
                print(
                    f"{i:2d}. {issue.get('message', 'N/A')[:70]}"
                )
                print(f"    Fichier: {issue.get('component', 'N/A')}")
                print()

        elif choice == "3":
            issue_type = input("Type (BUG/CODE_SMELL/VULNERABILITY): ").strip().upper()
            issues = monitor.get_issues(issue_type=issue_type)
            print(f"\n📋 Issues de type {issue_type} ({len(issues)} total)")
            print("-" * 70)
            for i, issue in enumerate(issues[:10], 1):
                print(
                    f"{i:2d}. {issue.get('message', 'N/A')[:70]}"
                )
                print(f"    Règle: {issue.get('rule', 'N/A')}")
                print()

        elif choice == "4":
            local_coverage = monitor.get_local_coverage()
            if local_coverage:
                print("\n📊 Couverture de test (depuis coverage.xml)")
                print("-" * 70)
                for key, value in local_coverage.items():
                    print(f"{key:20s}: {value}")
            else:
                print("❌ Aucun fichier coverage.xml trouvé")

        elif choice == "5":
            filename = input("Nom du fichier (défaut: sonar_report.json): ").strip()
            if not filename:
                filename = "sonar_report.json"
            monitor.export_json(filename)

        elif choice == "6":
            print("🔄 Rafraîchissement des données...")
            monitor.print_summary()

        elif choice == "0":
            print("👋 Au revoir!")
            break

        else:
            print("❌ Option invalide")


def main():
    """Point d'entrée principal"""
    print("🚀 SonarCloud Monitor v1.0")
    print("=" * 70)

    # Créer le monitor
    monitor = SonarMonitor()

    # Mode automatique
    if "--auto" in sys.argv:
        print("📊 MODE AUTOMATIQUE\n")
        result = monitor.print_summary()
        print("\n✅ Données récupérées avec succès!")
        return 0

    # Mode JSON
    if "--json" in sys.argv:
        monitor.export_json()
        print("✅ Rapport JSON créé!")
        return 0

    # Mode interactif par défaut
    try:
        result = monitor.print_summary()
        interactive_loop(monitor)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
