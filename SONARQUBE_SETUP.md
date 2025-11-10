# Configuration de SonarQube avec ton compte Consultator

## Étapes pour configurer le CI/CD SonarQube

### 1. Récupère ton token SonarCloud depuis le compte Consultator

1. Va sur: https://sonarcloud.io/account/security
2. Conecte-toi avec ton compte ericfunman
3. Tu devrais voir un token existant ou tu peux en créer un nouveau
4. Copie ce token (ex: `squ_...`)

### 2. Configure les Secrets GitHub

1. Va sur: https://github.com/ericfunman/boursicotor/settings/secrets/actions
2. Clique sur "New repository secret"
3. Ajoute ces deux secrets:

**Secret 1:**
- Name: `SONAR_HOST_URL`
- Value: `https://sonarcloud.io`

**Secret 2:**
- Name: `SONAR_TOKEN`
- Value: `<ton_token_sonarcloud>`

### 3. Configure le projet dans SonarCloud

Option A - Ajouter un nouveau projet:
1. Va sur: https://sonarcloud.io/projects
2. Clique sur "Analyze new project"
3. Sélectionne le repo `boursicotor`
4. Clique sur "Set Up"

Option B - Utiliser le projet existant (Consultator):
1. La clé de projet est: `ericfunman_Consultator`
2. Pour utiliser cette clé, change dans le workflow:
   ```yaml
   -Dsonar.projectKey=ericfunman_Consultator
   ```

### Changement du workflow pour utiliser ton compte existant

Modifie le job SonarQube dans `.github/workflows/ci-cd.yml`:

```yaml
- name: SonarQube Scan
  if: secrets.SONAR_TOKEN != ''
  uses: SonarSource/sonarqube-scan-action@master
  env:
    SONAR_HOST_URL: https://sonarcloud.io
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  with:
    args: >
      -Dsonar.projectKey=boursicotor
      -Dsonar.projectName=Boursicotor
      -Dsonar.sources=backend,frontend
      -Dsonar.tests=tests
      -Dsonar.coverage.exclusions=tests/**
      -Dsonar.python.coverage.reportPath=coverage.xml
```

## Après configuration des secrets

1. Valide que les secrets sont configurés: https://github.com/ericfunman/boursicotor/settings/secrets/actions
2. Fais un commit/push pour déclencher le workflow
3. Vérifie dans GitHub Actions que le job test passe ✅
4. Ensuite le job sonarqube se lancera et publiera les résultats sur SonarCloud

## Vérification du statut

- GitHub Actions: https://github.com/ericfunman/boursicotor/actions
- SonarCloud: https://sonarcloud.io/projects
- Cherche le projet `boursicotor` ou `ericfunman_Consultator`
