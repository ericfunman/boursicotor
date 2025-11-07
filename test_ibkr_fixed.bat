@echo off
cd "c:\Users\Eric LAPINA\Documents\Boursicotor"
echo Test de la collecte IBKR après correction des dépendances
echo.

python -c "
import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

print('🔍 Test de la fonctionnalité IBKR après correction...')
print()

try:
    from backend.ibkr_collector import IBKRCollector
    print('✅ 1. Import IBKRCollector: RÉUSSI')
except Exception as e:
    print(f'❌ 1. Import IBKRCollector: ÉCHEC - {e}')
    exit(1)

try:
    from backend.tasks import collect_data_ibkr
    print('✅ 2. Import collect_data_ibkr: RÉUSSI')
except Exception as e:
    print(f'❌ 2. Import collect_data_ibkr: ÉCHEC - {e}')
    exit(1)

try:
    collector = IBKRCollector()
    print('✅ 3. Création instance IBKRCollector: RÉUSSI')
except Exception as e:
    print(f'❌ 3. Création instance IBKRCollector: ÉCHEC - {e}')
    exit(1)

print()
print('🎉 Toutes les dépendances sont maintenant installées!')
print('💡 La collecte IBKR devrait maintenant fonctionner dans les workers Celery.')
print()
print('📋 Prochaines étapes:')
print('   1. Redémarrer les workers Celery si nécessaire')
print('   2. Tester une collecte IBKR depuis l\'interface Streamlit')
print('   3. Vérifier les logs pour confirmer que tout fonctionne')
"

pause