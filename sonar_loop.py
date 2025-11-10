#!/usr/bin/env python3
"""
Integrated Sonar Monitor & Auto-Fixer
Récupère issues SonarCloud + coverage en boucle et propose des corrections.

Usage:
    python sonar_loop.py                    # Mode interactif complet
    python sonar_loop.py --batch            # Mode batch
    python sonar_loop.py --watch            # Mode watch (rafraîchit toutes les 60s)
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from xml.etree import ElementTree as ET

# Importer les modules custom
try:
    from sonar_monitor import SonarMonitor
    from auto_fix_sonar import SonarAutoFixer
except ImportError:
    print("❌ Erreur: sonar_monitor.py et auto_fix_sonar.py doivent être dans le même répertoire")
    sys.exit(1)


class SonarLoopManager:
    """Gestionnaire de boucle de correction SonarCloud"""

    def __init__(self):
        self.monitor = SonarMonitor()
        self.fixer = SonarAutoFixer()
        self.iteration = 0
        self.history = []

    def get_coverage_summary(self) -> Dict:
        """Récupère un résumé de couverture"""
        coverage_file = Path("coverage.xml")

        if not coverage_file.exists():
            return {"available": False, "message": "No coverage.xml found"}

        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            lines_valid = int(root.get("lines-valid", 0))
            lines_covered = int(root.get("lines-covered", 0))
            line_rate = float(root.get("line-rate", 0))

            return {
                "available": True,
                "lines_valid": lines_valid,
                "lines_covered": lines_covered,
                "line_rate": round(line_rate * 100, 2),
                "message": f"{lines_covered}/{lines_valid} lines covered ({line_rate * 100:.1f}%)",
            }
        except Exception as e:
            return {"available": False, "message": f"Error: {e}"}

    def run_tests(self) -> bool:
        """Lance les tests avec pytest"""
        print("\n🧪 Running tests...")
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout + result.stderr

            # Parser les résultats
            if "passed" in output:
                print("✅ Tests ran successfully")
                print(output.split("\n")[-3:-1])  # Afficher les 2 dernières lignes
                return True
            else:
                print("❌ Tests failed or not found")
                return False
        except Exception as e:
            print(f"⚠️  Could not run tests: {e}")
            return False

    def generate_coverage(self) -> bool:
        """Génère un rapport de couverture"""
        print("\n📊 Generating coverage report...")
        try:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/",
                    "--cov=backend",
                    "--cov=frontend",
                    "--cov-report=xml",
                    "-q",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0 or "passed" in result.stdout:
                print("✅ Coverage report generated")
                coverage = self.get_coverage_summary()
                if coverage["available"]:
                    print(f"   {coverage['message']}")
                return True
            else:
                print("⚠️  Coverage generation issue")
                return False
        except Exception as e:
            print(f"❌ Error generating coverage: {e}")
            return False

    def print_loop_header(self):
        """Affiche l'en-tête de la boucle"""
        print("\n" + "=" * 80)
        print(f"🔄 SONAR LOOP - ITERATION #{self.iteration}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def print_loop_summary(self, issues: List, coverage: Dict):
        """Affiche un résumé de la boucle"""
        print("\n" + "─" * 80)
        print("📊 LOOP SUMMARY")
        print("─" * 80)

        # Issues
        severity_count = {}
        for issue in issues:
            sev = issue.get("severity", "UNKNOWN")
            severity_count[sev] = severity_count.get(sev, 0) + 1

        print("\n📋 Issues by severity:")
        for sev in ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]:
            count = severity_count.get(sev, 0)
            if count > 0:
                icon = "🔴" if sev == "BLOCKER" else (
                    "🟠" if sev == "CRITICAL" else (
                        "🟡" if sev == "MAJOR" else "🔵"
                    )
                )
                print(f"  {icon} {sev:10s}: {count:3d}")

        print(f"\n  📊 TOTAL: {len(issues)}")

        # Coverage
        print("\n📈 Test Coverage:")
        cov_summary = self.get_coverage_summary()
        if cov_summary["available"]:
            print(f"  ✅ {cov_summary['message']}")
        else:
            print(f"  ⚠️  {cov_summary['message']}")

        # Trends
        if self.history:
            prev = self.history[-1]
            prev_issues = prev.get("issues_count", 0)
            issue_delta = len(issues) - prev_issues

            if issue_delta < 0:
                print(f"\n📉 Trend: {issue_delta} issues (IMPROVING ✅)")
            elif issue_delta > 0:
                print(f"\n📈 Trend: +{issue_delta} issues (DEGRADING ❌)")
            else:
                print(f"\n➡️  Trend: No change in issue count (STABLE ➡️)")

    def interactive_loop(self):
        """Boucle interactive complète"""
        while True:
            self.iteration += 1
            self.print_loop_header()

            # Récupérer les données
            print("🔄 Fetching SonarCloud data...")
            issues = self.monitor.get_issues()
            coverage = self.get_coverage_summary()

            # Afficher le résumé
            self.print_loop_summary(issues, coverage)

            # Sauvegarder dans l'historique
            self.history.append({
                "iteration": self.iteration,
                "timestamp": datetime.now().isoformat(),
                "issues_count": len(issues),
                "coverage": coverage,
            })

            # Proposer les actions
            print("\n" + "─" * 80)
            print("🎯 ACTIONS")
            print("─" * 80)
            print("1. View all issues")
            print("2. Fix top issues")
            print("3. Run tests")
            print("4. Generate coverage report")
            print("5. View coverage details")
            print("6. Export report")
            print("7. Next iteration")
            print("0. Exit")

            action = input("\n👉 Action: ").strip()

            if action == "1":
                print("\n📋 Issues:")
                for i, issue in enumerate(issues[:20], 1):
                    print(f"{i:2d}. [{issue.get('severity'):8s}] {issue.get('message')[:60]}")
                    print(f"    {issue.get('component')}:{issue.get('line', '?')}")
                if len(issues) > 20:
                    print(f"... and {len(issues) - 20} more")

            elif action == "2":
                print("\n🔧 Proposing fixes...")
                # Grouper par règle et afficher les top
                rules = {}
                for issue in issues:
                    rule = issue.get("rule", "UNKNOWN")
                    rules[rule] = rules.get(rule, 0) + 1

                for rule, count in sorted(rules.items(), key=lambda x: -x[1])[:5]:
                    print(f"  • {rule}: {count} issues")

            elif action == "3":
                self.run_tests()

            elif action == "4":
                self.generate_coverage()

            elif action == "5":
                cov = self.get_coverage_summary()
                if cov["available"]:
                    print(f"\n📊 Coverage Details:")
                    print(f"  Lines valid:   {cov.get('lines_valid', 'N/A')}")
                    print(f"  Lines covered: {cov.get('lines_covered', 'N/A')}")
                    print(f"  Rate:          {cov.get('line_rate', 'N/A')}%")
                else:
                    print(f"\n❌ {cov['message']}")

            elif action == "6":
                filename = input("Filename (default: sonar_loop_report.json): ").strip()
                if not filename:
                    filename = "sonar_loop_report.json"

                report = {
                    "iterations": len(self.history),
                    "history": self.history,
                    "latest_issues_count": len(issues),
                    "latest_coverage": coverage,
                }

                with open(filename, "w") as f:
                    json.dump(report, f, indent=2)
                print(f"✅ Report saved: {filename}")

            elif action == "7":
                print("➡️  Next iteration...\n")
                continue

            elif action == "0":
                print("👋 Exiting")
                break

            else:
                print("❌ Invalid action")

    def batch_mode(self):
        """Mode batch - une exécution"""
        self.iteration = 1
        self.print_loop_header()

        print("🔄 Fetching data...")
        issues = self.monitor.get_issues()
        coverage = self.get_coverage_summary()

        self.print_loop_summary(issues, coverage)

        # Exporter le rapport
        report = {
            "timestamp": datetime.now().isoformat(),
            "issues_count": len(issues),
            "issues": issues,
            "coverage": coverage,
        }

        with open("sonar_batch_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n✅ Report saved: sonar_batch_report.json")
        return 0

    def watch_mode(self, interval: int = 60):
        """Mode watch - rafraîchit tous les N secondes"""
        print(f"👁️  WATCH MODE - Refreshing every {interval}s")
        print("Press Ctrl+C to exit\n")

        iteration = 0
        try:
            while True:
                iteration += 1
                print(f"\n{'=' * 80}")
                print(f"⏰ Check #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 80)

                issues = self.monitor.get_issues()
                coverage = self.get_coverage_summary()

                severity_count = {}
                for issue in issues:
                    severity_count[issue.get("severity", "?")] = (
                        severity_count.get(issue.get("severity", "?"), 0) + 1
                    )

                print(f"📋 Issues: {len(issues)}")
                print(f"   Blocker: {severity_count.get('BLOCKER', 0)}")
                print(f"   Critical: {severity_count.get('CRITICAL', 0)}")
                print(f"   Major: {severity_count.get('MAJOR', 0)}")
                print(f"📈 Coverage: {coverage.get('line_rate', '?')}%")

                print(f"\n⏳ Next check in {interval}s...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 Exiting watch mode")
            return 0


def main():
    """Point d'entrée"""
    print("🚀 Sonar Integrated Loop Manager v1.0")
    print("=" * 80)

    manager = SonarLoopManager()

    if "--batch" in sys.argv:
        print("📊 BATCH MODE")
        return manager.batch_mode()
    elif "--watch" in sys.argv:
        interval = 60
        if "--interval" in sys.argv:
            idx = sys.argv.index("--interval")
            if idx + 1 < len(sys.argv):
                try:
                    interval = int(sys.argv[idx + 1])
                except ValueError:
                    pass
        return manager.watch_mode(interval)
    else:
        print("🔄 INTERACTIVE MODE")
        manager.interactive_loop()
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted")
        sys.exit(1)
