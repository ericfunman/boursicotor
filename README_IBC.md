# Installation automatique d'IBC (IB Controller)

## Qu'est-ce qu'IBC ?

IBC (IB Controller) est un outil qui permet de lancer automatiquement IB Gateway et de remplir les credentials de connexion, éliminant ainsi le besoin de connexion manuelle.

## Installation

### Prérequis

- IB Gateway installé (C:\Jts\ibgateway\1037)
- Fichier `ibgateway_config.ini` configuré avec vos identifiants
- Connexion Internet pour télécharger IBC

### Étapes d'installation

1. **Exécuter le script d'installation automatique** :
   ```batch
   install_ibc.bat
   ```

2. Le script va :
   - Télécharger IBC version 3.20.0 depuis GitHub
   - L'installer dans `C:\IBC`
   - Créer automatiquement la configuration à partir de `ibgateway_config.ini`
   - Générer un script de lancement `C:\IBC\start_gateway.bat`

3. **C'est tout !** Le script `startBoursicotor.bat` détectera automatiquement IBC et l'utilisera.

## Utilisation

### Avec IBC (automatique)

Lancez simplement :
```batch
startBoursicotor.bat
```

IB Gateway se lancera et se connectera automatiquement avec vos identifiants. Vous n'avez plus besoin de cliquer sur "Login".

### Sans IBC (manuel - fallback)

Si IBC n'est pas installé, le script vous proposera de continuer en mode manuel. Vous devrez alors :
1. Entrer vos identifiants manuellement dans IB Gateway
2. Cliquer sur "Login"
3. Appuyer sur une touche pour continuer le script

## Configuration

La configuration IBC est générée automatiquement à partir de `ibgateway_config.ini` :

```ini
Username=ericlapinasimu
Password=bouh806simu
TradingMode=paper
Port=4002
```

Le fichier de configuration IBC est créé dans : `C:\IBC\config.ini`

### Options avancées

Si vous souhaitez modifier la configuration IBC, éditez `C:\IBC\config.ini` :

- `TradingMode` : `paper` (simulation) ou `live` (réel)
- `IbApiPort` : Port API (4002 pour paper, 4001 pour live)
- `MinimizeMainWindow` : `yes` pour réduire la fenêtre IB Gateway
- `AcceptIncomingConnectionAction` : `accept` pour accepter automatiquement les connexions API

## Désinstallation

Pour désinstaller IBC :
1. Supprimez le dossier `C:\IBC`
2. Le script `startBoursicotor.bat` reviendra automatiquement au mode manuel

## Dépannage

### "IBC non installé"
- Vérifiez que `C:\IBC\start_gateway.bat` existe
- Réexécutez `install_ibc.bat`

### "Failed to download IBC"
- Vérifiez votre connexion Internet
- Le script télécharge depuis : https://github.com/IbcAlpha/IBC/releases/

### IB Gateway ne se connecte pas automatiquement
- Vérifiez que `ibgateway_config.ini` contient les bons identifiants
- Vérifiez `C:\IBC\config.ini` pour la configuration IBC
- Consultez les logs IBC dans `C:\IBC\Logs`

### "Username not found in config file"
- Assurez-vous que `ibgateway_config.ini` existe et contient :
  ```ini
  Username=votre_username
  Password=votre_password
  TradingMode=paper
  Port=4002
  ```

## Sécurité

⚠️ **IMPORTANT** : Les fichiers suivants contiennent vos identifiants et sont exclus de Git :
- `ibgateway_config.ini` (vos credentials)
- `C:\IBC\config.ini` (configuration IBC avec credentials)
- `C:\IBC\` (dossier complet exclu de Git)

Ne commitez JAMAIS ces fichiers !

## Versions

- IBC : 3.20.0 (dernière version stable)
- Compatible avec : IB Gateway 10.37

## Références

- [IBC sur GitHub](https://github.com/IbcAlpha/IBC)
- [Documentation IBC](https://github.com/IbcAlpha/IBC/blob/master/userguide.md)
