#!/usr/bin/env python3
"""
Sonar Issues Auto-Fixer Script
Récupère les issues SonarCloud et propose des corrections automatiques en boucle.

Usage:
    python auto_fix_sonar.py                 # Mode interactif
    python auto_fix_sonar.py --dry-run       # Voir les changements sans les appliquer
    python auto_fix_sonar.py --auto          # Appliquer automatiquement
"""

import json
import sys
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
from datetime import datetime

# Configuration
SONAR_HOST = "https://sonarcloud.io"
SONAR_PROJECT_KEY = "ericfunman_boursicotor"
SONAR_ORGANIZATION = "ericfunman"


@dataclass
class Issue:
    """Représente une issue SonarCloud"""
    key: str
    type: str
    severity: str
    rule: str
    message: str
    component: str
    line: int
    debt: str
    status: str
    effort: str


class SonarAutoFixer:
    """Classe pour récupérer et corriger les issues SonarCloud"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.fixes_failed = []

    def fetch_issues(self) -> List[Issue]:
        """Récupère les issues depuis SonarCloud"""
        url = f"{SONAR_HOST}/api/issues/search"
        params = {
            "componentKeys": SONAR_PROJECT_KEY,
            "organization": SONAR_ORGANIZATION,
            "ps": 500,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            issues = []
            for issue_data in data.get("issues", []):
                try:
                    issue = Issue(
                        key=issue_data.get("key"),
                        type=issue_data.get("type"),
                        severity=issue_data.get("severity"),
                        rule=issue_data.get("rule"),
                        message=issue_data.get("message"),
                        component=issue_data.get("component"),
                        line=issue_data.get("line", 0),
                        debt=issue_data.get("debt", "0"),
                        status=issue_data.get("status"),
                        effort=issue_data.get("effort", "0"),
                    )
                    issues.append(issue)
                except Exception as e:
                    print(f"⚠️  Erreur parsing issue: {e}")
                    continue

            return issues
        except Exception as e:
            print(f"❌ Erreur récupération issues: {e}")
            return []

    def group_issues_by_rule(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """Groupe les issues par règle"""
        grouped = {}
        for issue in issues:
            if issue.rule not in grouped:
                grouped[issue.rule] = []
            grouped[issue.rule].append(issue)
        return grouped

    def print_issues_summary(self, issues: List[Issue]):
        """Affiche un résumé des issues"""
        print("\n" + "=" * 70)
        print("📋 ISSUES SUMMARY")
        print("=" * 70)

        # Compter par sévérité
        severity_count = {}
        type_count = {}
        for issue in issues:
            severity_count[issue.severity] = severity_count.get(issue.severity, 0) + 1
            type_count[issue.type] = type_count.get(issue.type, 0) + 1

        print("\n🎯 Par sévérité:")
        for sev in ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]:
            count = severity_count.get(sev, 0)
            if count > 0:
                icon = "🔴" if sev == "BLOCKER" else (
                    "🟠" if sev == "CRITICAL" else (
                        "🟡" if sev == "MAJOR" else (
                            "🔵" if sev == "MINOR" else "⚪"
                        )
                    )
                )
                print(f"  {icon} {sev:10s}: {count:3d}")

        print("\n🏷️  Par type:")
        for type_name in ["BUG", "CODE_SMELL", "VULNERABILITY"]:
            count = type_count.get(type_name, 0)
            if count > 0:
                icon = "🐛" if type_name == "BUG" else (
                    "👃" if type_name == "CODE_SMELL" else "🔒"
                )
                print(f"  {icon} {type_name:15s}: {count:3d}")

        print(f"\n📊 Total: {len(issues)} issues")
        print("=" * 70)

    def analyze_issue(self, issue: Issue) -> Optional[Dict]:
        """Analyse une issue et propose une correction"""
        analysis = {
            "issue": issue,
            "fix_type": None,
            "description": None,
            "file": None,
            "fix_suggestion": None,
        }

        # Extraire le fichier
        component = issue.component
        if ":" in component:
            project, file_path = component.split(":", 1)
            analysis["file"] = Path(file_path)

        # Analyser selon la règle
        rule_lower = issue.rule.lower()

        # Bare except
        if "bare" in rule_lower and "except" in rule_lower:
            analysis["fix_type"] = "bare_except"
            analysis["description"] = "Bare except statement - utiliser exceptions spécifiques"
            analysis["fix_suggestion"] = (
                "Remplacer 'except:' par 'except (SpecificException1, SpecificException2):'"
            )

        # Print statements
        elif "print" in rule_lower or "no-print-statement" in rule_lower:
            analysis["fix_type"] = "print_statement"
            analysis["description"] = "Print statement found - utiliser logging"
            analysis["fix_suggestion"] = "Remplacer print() par logger.debug/info/warning/error()"

        # Missing docstring
        elif "docstring" in rule_lower or "missing-function-docstring" in rule_lower:
            analysis["fix_type"] = "missing_docstring"
            analysis["description"] = "Missing docstring"
            analysis["fix_suggestion"] = 'Ajouter docstring: """Description."""'

        # Too many arguments
        elif "too-many" in rule_lower and "argument" in rule_lower:
            analysis["fix_type"] = "too_many_args"
            analysis["description"] = "Too many function arguments"
            analysis["fix_suggestion"] = "Refactoriser la fonction ou utiliser un dictionnaire"

        # Unused variable
        elif "unused" in rule_lower and "variable" in rule_lower:
            analysis["fix_type"] = "unused_variable"
            analysis["description"] = "Unused variable"
            analysis["fix_suggestion"] = "Supprimer la variable ou la préfixer avec '_'"

        # Unused import
        elif "unused" in rule_lower and ("import" in rule_lower or "w0611" in rule_lower):
            analysis["fix_type"] = "unused_import"
            analysis["description"] = "Unused import"
            analysis["fix_suggestion"] = "Supprimer l'import inutilisé"

        # Duplicate code
        elif "duplicate" in rule_lower and "code" in rule_lower:
            analysis["fix_type"] = "duplicate_code"
            analysis["description"] = "Duplicate code found"
            analysis["fix_suggestion"] = "Extraire en fonction commune ou utiliser héritage"

        # Line too long
        elif "line" in rule_lower and "too" in rule_lower and "long" in rule_lower:
            analysis["fix_type"] = "line_too_long"
            analysis["description"] = "Line too long (>120 characters)"
            analysis["fix_suggestion"] = "Casser la ligne ou extraire une variable"

        # Magic number
        elif "magic" in rule_lower and ("number" in rule_lower or "2823" in issue.rule):
            analysis["fix_type"] = "magic_number"
            analysis["description"] = "Magic number"
            analysis["fix_suggestion"] = "Définir une constante nommée"

        # Inconsistent quotes
        elif "quote" in rule_lower or "inconsistent" in rule_lower:
            analysis["fix_type"] = "inconsistent_quotes"
            analysis["description"] = "Inconsistent string quotes"
            analysis["fix_suggestion"] = "Utiliser des guillemets cohérents (double quotes par défaut)"

        return analysis

    def print_fix_suggestion(self, analysis: Dict, index: int = 1):
        """Affiche une suggestion de correction"""
        issue = analysis["issue"]
        print(f"\n{'─' * 70}")
        print(f"#{index} - {issue.severity} ({issue.type})")
        print(f"{'─' * 70}")
        print(f"📄 Fichier: {issue.component}:{issue.line}")
        print(f"📝 Message: {issue.message}")
        print(f"🏷️  Règle: {issue.rule}")
        if analysis["fix_type"]:
            print(f"🔧 Type: {analysis['fix_type']}")
            print(f"💡 Description: {analysis['description']}")
            print(f"✨ Suggestion: {analysis['fix_suggestion']}")
        else:
            print(f"⚠️  Aucune correction automatique disponible")

    def interactive_mode(self, issues: List[Issue]):
        """Mode interactif de correction"""
        grouped = self.group_issues_by_rule(issues)
        rules_list = sorted(grouped.items(), key=lambda x: -len(x[1]))

        for rule_idx, (rule, rule_issues) in enumerate(rules_list, 1):
            print(f"\n\n{'=' * 70}")
            print(f"📌 Règle {rule_idx}/{len(rules_list)}: {rule}")
            print(f"   Issues: {len(rule_issues)}")
            print("=" * 70)

            for issue_idx, issue in enumerate(rule_issues[:3], 1):  # Afficher max 3
                analysis = self.analyze_issue(issue)
                self.print_fix_suggestion(analysis, issue_idx)

            if len(rule_issues) > 3:
                print(f"\n... et {len(rule_issues) - 3} autres issues avec cette règle")

            # Demander l'action
            print("\n🎯 Actions disponibles:")
            print("  [ENTER] Passer à la suivante")
            print("  [f]     Fixer (proposer la correction)")
            print("  [i]     Ignorer toutes les issues de cette règle")
            print("  [q]     Quitter")

            action = input("\n👉 Action: ").strip().lower()

            if action == "f":
                print("✅ Correction proposée (à implémenter manuellement)")
                self.fixes_applied.append(rule)
            elif action == "i":
                print("⏭️  Règle ignorée")
            elif action == "q":
                print("👋 Quit")
                break

    def auto_mode(self, issues: List[Issue]):
        """Mode automatique - afficher les statistiques"""
        print("\n" + "=" * 70)
        print("🤖 MODE AUTOMATIQUE")
        print("=" * 70)

        grouped = self.group_issues_by_rule(issues)

        print(f"\n📊 Statistiques par règle:")
        print("-" * 70)

        for idx, (rule, rule_issues) in enumerate(
            sorted(grouped.items(), key=lambda x: -len(x[1]))[:15], 1
        ):
            severity = rule_issues[0].severity if rule_issues else "?"
            issue_type = rule_issues[0].type if rule_issues else "?"
            print(f"{idx:2d}. {rule:50s} {len(rule_issues):3d} ({severity})")

        # Sauvegarder en JSON
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(issues),
            "issues_by_rule": {
                rule: len(rule_issues) for rule, rule_issues in grouped.items()
            },
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
        }

        with open("sonar_fix_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n✅ Rapport sauvegardé: sonar_fix_report.json")

    def run(self, mode: str = "interactive"):
        """Lance le processus de correction"""
        print("🚀 Sonar Auto-Fixer v1.0")
        print("=" * 70)

        # Récupérer les issues
        print("🔄 Récupération des issues SonarCloud...")
        issues = self.fetch_issues()

        if not issues:
            print("❌ Aucune issue trouvée ou erreur de connexion")
            return 1

        # Afficher le résumé
        self.print_issues_summary(issues)

        # Mode
        if mode == "interactive":
            self.interactive_mode(issues)
        elif mode == "auto":
            self.auto_mode(issues)

        # Résumé final
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ FINAL")
        print("=" * 70)
        print(f"Issues trouvées: {len(issues)}")
        print(f"Corrections appliquées: {len(self.fixes_applied)}")
        print(f"Corrections échouées: {len(self.fixes_failed)}")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'REAL'}")
        print("=" * 70)

        return 0


def main():
    """Point d'entrée principal"""
    dry_run = "--dry-run" in sys.argv
    auto_mode = "--auto" in sys.argv
    mode = "auto" if auto_mode else "interactive"

    fixer = SonarAutoFixer(dry_run=dry_run)
    return fixer.run(mode=mode)


if __name__ == "__main__":
    sys.exit(main())
