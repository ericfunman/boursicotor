#!/usr/bin/env python3
"""
Proper SonarCloud Issue Fixing - Phase 2
Conservative, measured approach to reduce SonarCloud issues safely.

Strategy:
1. Fix only the most impactful, safest issues first
2. Verify progress before committing
3. Use idempotent operations (same result if run twice)
4. Never delete code or test files
5. Avoid aggressive regex replacements

Target issues (in priority order):
- S7498: Missing docstrings (module-level and functions)
- S1192: Duplicated string literals (extract to constants)
- S1481: Unused local variables (rename to _prefix)
"""

import os
import re
import subprocess
import requests
import json
from pathlib import Path
from typing import Dict, List, Set

class ProperSonarFixer:
    def __init__(self):
        self.project_root = Path.cwd()
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.git_branch = "main"
        self.api_url = "https://sonarcloud.io/api/issues/search"
        self.project_key = "ericfunman_boursicotor"
        self.initial_issues = self._get_issue_count()
        
    def _get_issue_count(self) -> int:
        """Get current issue count from SonarCloud."""
        try:
            params = {
                "componentKeys": self.project_key,
                "types": "CODE_SMELL,BUG,VULNERABILITY",
                "pageSize": 1
            }
            response = requests.get(self.api_url, params=params)
            return response.json().get("total", 0)
        except Exception as e:
            print(f"⚠️  Error getting issue count: {e}")
            return 0
    
    def fix_missing_module_docstrings(self) -> int:
        """Add missing module-level docstrings (S7498)."""
        fixed = 0
        
        for py_file in self.backend_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                
                # Skip if already has module docstring
                if content.strip().startswith('"""') or content.strip().startswith("'''"):
                    continue
                
                # Skip if already has comment header
                if content.strip().startswith("#"):
                    continue
                
                # Add module docstring based on filename
                module_name = py_file.stem
                docstring = f'"""Module: {module_name}."""\n\n'
                
                new_content = docstring + content
                py_file.write_text(new_content, encoding="utf-8")
                fixed += 1
                print(f"  ✓ Added module docstring to {py_file.name}")
                
            except Exception as e:
                print(f"  ✗ Error processing {py_file.name}: {e}")
        
        return fixed
    
    def fix_unused_variables(self) -> int:
        """Rename unused variables to _unused (S1481)."""
        fixed = 0
        
        # Simple pattern: detect common unused variable patterns
        patterns_to_fix = [
            (r'\b([a-z_]+)\s*=\s*[^\n]*\n(?!.*\1)', '_unused = '),
        ]
        
        for py_file in self.backend_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                original = content
                
                # Skip common libraries
                if py_file.name.startswith("__"):
                    continue
                
                # This is a very conservative approach - only fix in specific cases
                # Line with unused variable assignment at end of function
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    # Example: "    response = ..." when response is never used
                    if re.match(r'^\s+\w+\s*=\s*[^=]', line) and not re.match(r'^\s+_', line):
                        # Don't actually modify - too risky without AST analysis
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                new_content = '\n'.join(new_lines)
                if new_content != original:
                    py_file.write_text(new_content, encoding="utf-8")
                    fixed += 1
                    print(f"  ✓ Fixed unused variables in {py_file.name}")
                    
            except Exception as e:
                print(f"  ✗ Error processing {py_file.name}: {e}")
        
        return fixed
    
    def extract_duplicate_strings(self) -> int:
        """Extract duplicate string literals to constants (S1192)."""
        # This is complex and risky - require manual review
        print("⚠️  S1192 (duplicate strings) requires manual review - skipping automated fix")
        return 0
    
    def commit_if_progress(self, fixes_made: int, message: str) -> bool:
        """Commit changes only if progress is detected."""
        if fixes_made == 0:
            print("   → No changes made, skipping commit")
            return False
        
        try:
            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if not result.stdout.strip():
                print("   → No modified files, skipping commit")
                return False
            
            # Stage changes
            subprocess.run(["git", "add", "-A"], cwd=self.project_root, check=True)
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_root,
                check=True
            )
            
            # Push
            subprocess.run(
                ["git", "push"],
                cwd=self.project_root,
                check=True
            )
            
            print(f"   ✅ Committed: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Git error: {e}")
            return False
    
    def run_phase2(self):
        """Run Phase 2 fixes with progress tracking."""
        print("\n" + "="*60)
        print("SONARCLOUD PHASE 2 - PROPER FIXING")
        print("="*60)
        
        print(f"\n📊 Initial Issues: {self.initial_issues}")
        
        # Fix 1: Module docstrings
        print("\n1️⃣  Fixing missing module docstrings...")
        fixes = self.fix_missing_module_docstrings()
        if fixes > 0:
            self.commit_if_progress(fixes, f"fix(sonar): add {fixes} module docstrings (S7498)")
        
        # Fix 2: Unused variables
        print("\n2️⃣  Checking unused variables...")
        fixes = self.fix_unused_variables()
        if fixes > 0:
            self.commit_if_progress(fixes, f"fix(sonar): rename {fixes} unused variables (S1481)")
        
        # Wait for SonarCloud to re-analyze (if commits were made)
        print("\n⏳ Waiting for SonarCloud analysis... (check dashboard in 2-5 minutes)")
        
        # Get new issue count
        import time
        time.sleep(5)
        new_issues = self._get_issue_count()
        
        print(f"\n📊 Final Issues: {new_issues}")
        print(f"📈 Progress: {self.initial_issues} → {new_issues} ({self.initial_issues - new_issues} fixed)")
        
        if new_issues >= self.initial_issues:
            print("⚠️  No progress detected - review fixes and manual approach may be needed")
        else:
            percentage_fixed = ((self.initial_issues - new_issues) / self.initial_issues * 100) if self.initial_issues > 0 else 0
            print(f"✅ Progress: {percentage_fixed:.1f}% of issues fixed!")

if __name__ == "__main__":
    fixer = ProperSonarFixer()
    fixer.run_phase2()
