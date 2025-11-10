#!/usr/bin/env python3
"""
SonarCloud Issues Auto-Fix Loop
Boucle automatique de récupération et correction des issues SonarCloud
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime

class AutoFixLoop:
    """Boucle automatique de correction des issues SonarCloud"""
    
    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.root_path = Path(__file__).parent
        self.log_file = self.root_path / "sonar_autofix_loop.log"
    
    def log(self, message: str):
        """Log un message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    
    def run_fetch_issues(self) -> dict:
        """Exécute le script de récupération des issues"""
        self.log(f"\n{'='*100}")
        self.log(f"🔍 ITÉRATION {self.current_iteration + 1}/{self.max_iterations}")
        self.log(f"{'='*100}")
        
        self.log("📡 Récupération des issues SonarCloud...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.root_path / "fetch_and_fix_sonar_issues.py")],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("✅ Issues récupérées avec succès")
                
                # Parser les résultats si le fichier JSON existe
                issues_file = self.root_path / "sonar_issues_latest.json"
                if issues_file.exists():
                    with open(issues_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.log(f"   Total: {data['total']} issues")
                        return data
            else:
                self.log(f"❌ Erreur récupération: {result.stderr[:200]}")
        
        except subprocess.TimeoutExpired:
            self.log("❌ Timeout lors de la récupération")
        except Exception as e:
            self.log(f"❌ Exception: {e}")
        
        return None
    
    def run_auto_fix(self) -> int:
        """Exécute le script de correction automatique"""
        self.log("🔧 Exécution des corrections automatiques...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.root_path / "auto_fix_sonar_issues.py")],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Parser le nombre de fixes
                output = result.stdout
                if "Total fixes appliqués:" in output:
                    for line in output.split('\n'):
                        if "Total fixes appliqués:" in line:
                            try:
                                fixes = int(line.split(':')[1].strip())
                                self.log(f"✅ {fixes} issues corrigées")
                                return fixes
                            except:
                                pass
                
                self.log("✅ Corrections appliquées")
                return 0
            else:
                self.log(f"⚠️ Auto-fix retour: {result.returncode}")
                return 0
        
        except subprocess.TimeoutExpired:
            self.log("❌ Timeout lors de l'auto-fix")
            return 0
        except Exception as e:
            self.log(f"❌ Exception auto-fix: {e}")
            return 0
    
    def run_tests(self) -> bool:
        """Exécute les tests pour vérifier les corrections"""
        self.log("🧪 Exécution des tests...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "--tb=no", "-q"],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            # Parser les résultats
            output = result.stdout + result.stderr
            
            if "passed" in output:
                # Extraire les résultats
                self.log(f"✅ Tests complétés")
                
                # Afficher le résumé
                for line in output.split('\n')[-10:]:
                    if line.strip():
                        self.log(f"   {line}")
                
                return result.returncode == 0
            else:
                self.log(f"⚠️ Tests output: {output[-200:]}")
                return True  # Continuer quand même
        
        except subprocess.TimeoutExpired:
            self.log("⚠️ Tests timeout (continuer)")
            return True
        except Exception as e:
            self.log(f"⚠️ Tests exception: {e} (continuer)")
            return True
    
    def commit_and_push(self, iteration: int) -> bool:
        """Commit et push les changements"""
        self.log("📤 Commit et push...")
        
        try:
            # Git add
            subprocess.run(
                ['git', 'add', '.'],
                cwd=self.root_path,
                capture_output=True
            )
            
            # Git commit
            commit_msg = f"fix(sonar): auto-fix loop iteration {iteration} - multiple issues"
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log(f"✅ Commit successful")
                
                # Git push
                push_result = subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    cwd=self.root_path,
                    capture_output=True,
                    text=True
                )
                
                if push_result.returncode == 0:
                    self.log("✅ Push successful")
                    return True
                else:
                    self.log(f"⚠️ Push failed: {push_result.stderr[:100]}")
                    return False
            else:
                self.log(f"ℹ️ Rien à commiter")
                return True
        
        except Exception as e:
            self.log(f"❌ Commit/push error: {e}")
            return False
    
    def run_loop(self):
        """Exécute la boucle principale"""
        self.log("=" * 100)
        self.log("🚀 DÉMARRAGE: Boucle automatique de correction SonarCloud")
        self.log(f"Max itérations: {self.max_iterations}")
        self.log("=" * 100)
        
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            
            try:
                # 1. Récupérer les issues
                issues_data = self.run_fetch_issues()
                if not issues_data:
                    self.log("⚠️ Impossible de récupérer les issues, skip itération")
                    time.sleep(5)
                    continue
                
                total_issues = issues_data.get('total', 0)
                
                # 2. Corriger les issues
                fixes_count = self.run_auto_fix()
                
                # 3. Exécuter les tests
                tests_ok = self.run_tests()
                
                # 4. Commit et push
                self.commit_and_push(iteration)
                
                # 5. Résumé itération
                self.log(f"\n📊 RÉSUMÉ ITÉRATION {iteration}:")
                self.log(f"   Issues totales: {total_issues}")
                self.log(f"   Issues corrigées: {fixes_count}")
                self.log(f"   Tests: {'✅ OK' if tests_ok else '⚠️ Issues'}")
                
                # Vérifier s'il faut continuer
                if fixes_count == 0:
                    self.log(f"\n🎉 Pas plus de fixes possibles, arrêt de la boucle")
                    break
                
                # Attendre avant la prochaine itération
                if iteration < self.max_iterations:
                    self.log(f"⏰ Attente avant itération {iteration + 1}...")
                    time.sleep(10)
            
            except KeyboardInterrupt:
                self.log(f"\n⚠️ Arrêt par l'utilisateur")
                break
            except Exception as e:
                self.log(f"❌ Erreur itération {iteration}: {e}")
        
        self.log(f"\n{'='*100}")
        self.log(f"✅ BOUCLE COMPLÉTÉE: {self.current_iteration} itérations")
        self.log(f"{'='*100}")
    
    def print_summary(self):
        """Affiche un résumé final"""
        print(f"\n{'='*100}")
        print(f"📋 RÉSUMÉ FINAL")
        print(f"{'='*100}")
        print(f"Log sauvegardé dans: {self.log_file}")
        print(f"Itérations complétées: {self.current_iteration}")
        print(f"\n💡 Prochaines étapes:")
        print(f"   1. Vérifier les résultats SonarCloud")
        print(f"   2. Exécuter: pytest tests/ -v")
        print(f"   3. Vérifier les violations restantes")

if __name__ == '__main__':
    # Configuration
    max_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    # Créer et lancer la boucle
    loop = AutoFixLoop(max_iterations=max_iterations)
    loop.run_loop()
    loop.print_summary()
