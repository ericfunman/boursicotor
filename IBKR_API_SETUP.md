# Configuration manuelle requise pour IB Gateway

## Problème
IB Gateway se lance avec l'option "Read-Only API" activée, ce qui bloque les requêtes d'écriture comme `reqMatchingSymbols()`.

## Solution - Configuration manuelle unique

### Étapes à suivre (une seule fois) :

1. **Fermer IB Gateway** s'il est en cours d'exécution
   ```
   taskkill /F /IM java.exe
   ```

2. **Lancer IB Gateway MANUELLEMENT** (pas via IBC)
   - Double-cliquez sur : `C:\Jts\ibgateway\1037\ibgateway.exe`
   - Connectez-vous avec : `ericlapinasimu` / `bouh806simu`
   - Choisissez : **Paper Trading**

3. **Configurer l'API**
   - Cliquez sur l'icône ⚙️ (Settings) en haut à droite
   - Allez dans : **API** → **Settings**
   - **DÉCOCHEZ** la case **"Read-Only API"**
   - Vérifiez que **"Enable ActiveX and Socket Clients"** est **COCHÉ**
   - Socket Port : **4002** (pour paper trading)
   - Cliquez sur **OK** pour sauvegarder

4. **Fermer IB Gateway**
   - Les paramètres sont maintenant sauvegardés

5. **Relancer via startBoursicotor.bat**
   - IBC utilisera maintenant les bons paramètres
   - Double-cliquez sur `startBoursicotor.bat`

## Vérification
- Si le message "Read-Only API" persiste, recommencez les étapes ci-dessus
- Les paramètres sont stockés dans : `C:\Jts\mcemhgaoihlllffaecddkfedignijlbeleknhnak\ibg.xml`

## Note importante
Cette configuration est **persistante** - vous ne devez la faire qu'**une seule fois**.
Par la suite, IBC lancera IB Gateway avec ces paramètres automatiquement.
