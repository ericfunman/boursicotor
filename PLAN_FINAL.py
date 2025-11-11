#!/usr/bin/env python3
"""
PLAN PRAGMATIQUE FINAL
Pour atteindre: 60% coverage + 0 Sonar errors
"""

PLAN = """
=============================================================================
PHASE 1: FIX les 158 Sonar issues RAPIDEMENT
=============================================================================

S1192 (40): Duplicated strings
  - Complexe: Demande refactoring du code
  - Action: Ignorer pour maintenant (trop d'impact)

S7498 (38): dict() -> {}
  - Facile: Simple regex replace
  - Action: Créer fixer et appliquer

S3776 (27): Cognitive complexity
  - Complexe: Demande refactoring des fonctions
  - Action: Ignorer pour maintenant

S1481 (16): Unused variables  
  - Facile: Remplacer par underscore
  - Action: Utiliser fixer existant

S117 (14): Variable naming conventions
  - Moyen: Renommer des variables
  - Action: Regex replace patterns spécifiques

Total facile: 38 + 16 = 54 issues (34%)
Reste complexe: 104 issues (66%)

=============================================================================
PHASE 2: COVERAGE tests rapides
=============================================================================

Coverage Locale: 13%
Coverage Sonar:  4.5% (en augmentation)

Pour atteindre 60%:
- Créer 50+ tests simples pour couvrir imports/paths critiques
- Focus sur backend/models.py (265 lignes, 0% couverture)
- Focus sur backend/security.py (138 lignes, 92% déjà - presque fini!)
- Focus sur backend/config.py (33 lignes, 0% - facile!)
- Focus sur backend/technical_indicators.py (163 lignes, 0%)

=============================================================================
ACTIONS IMMÉDIATES
=============================================================================

1. Fixer S7498 (dict -> {}) - 38 issues d'un coup
   - Fixer simple regex: dict() -> {}
   - Commit

2. Fixer S1481 (unused vars) - 16 issues
   - Run fix_s1481_unused.py
   - Commit

3. Augmenter couverture à 15-20%
   - Créer tests pour config, models, technical_indicators
   - Commit

4. Vérifier Sonar après chaque commit
   - Voir progression (issues baissent, coverage monte)

5. Boucler jusqu'à targets: 60% + 0 errors

=============================================================================
RÉSULTAT ATTENDU
=============================================================================

Après Phase 1: 158 - 54 = 104 issues restants (66%)
Après Phase 2: Coverage 13% -> 20%+

Puis: Fixer les 104 restants manuellement/partiellement
"""

print(PLAN)
