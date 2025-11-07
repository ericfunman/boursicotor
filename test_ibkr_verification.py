#!/usr/bin/env python3
"""
Test script to verify IBKR functionality after dependency fixes
"""
import os
import sys

# Set environment variables to suppress Streamlit warnings
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

print('🔍 Test de la fonctionnalité IBKR après correction...')
print()

def test_import(name, import_statement):
    """Test an import and report result"""
    try:
        exec(import_statement)
        print(f'✅ {name}: RÉUSSI')
        return True
    except Exception as e:
        print(f'❌ {name}: ÉCHEC - {e}')
        return False

# Test 1: Import IBKRCollector
success1 = test_import('1. Import IBKRCollector', 'from backend.ibkr_collector import IBKRCollector')

# Test 2: Import collect_data_ibkr task
success2 = test_import('2. Import collect_data_ibkr', 'from backend.tasks import collect_data_ibkr')

# Test 3: Create IBKRCollector instance
if success1:
    try:
        from backend.ibkr_collector import IBKRCollector
        collector = IBKRCollector()
        print('✅ 3. Création instance IBKRCollector: RÉUSSI')
        success3 = True
    except Exception as e:
        print(f'❌ 3. Création instance IBKRCollector: ÉCHEC - {e}')
        success3 = False
else:
    success3 = False

print()
if success1 and success2 and success3:
    print('🎉 Toutes les dépendances sont maintenant installées!')
    print('💡 La collecte IBKR devrait maintenant fonctionner dans les workers Celery.')
    print()
    print('📋 Prochaines étapes:')
    print('   1. Redémarrer les workers Celery si nécessaire')
    print('   2. Tester une collecte IBKR depuis l\'interface Streamlit')
    print('   3. Vérifier les logs pour confirmer que tout fonctionne')
    sys.exit(0)
else:
    print('❌ Certains tests ont échoué. Vérifiez les dépendances.')
    sys.exit(1)