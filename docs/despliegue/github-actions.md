# GitHub Actions

Actualmente el proyecto utiliza **Jenkins** como servidor de CI/CD. Los pipelines están definidos en los archivos `Jenkinsfile` del backend y frontend.

## Configuración Propuesta para GitHub Actions

Si se migra a GitHub Actions, la estructura sugerida sería:

```yaml
# .github/workflows/backend.yml
name: Backend CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest --cov=. --cov-report=xml
      - uses: sonarsource/sonarqube-scan-action@master
```

```yaml
# .github/workflows/frontend.yml
name: Frontend CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run test
      - run: npm run build
```

Para más detalles sobre el pipeline actual con Jenkins, ver [Pipeline CI/CD](pipeline.md).
