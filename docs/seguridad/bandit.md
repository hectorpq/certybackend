# Análisis de Seguridad Estática (Bandit)

## Descripción

Bandit es una herramienta SAST (Static Application Security Testing) para Python. Analiza el código en busca de vulnerabilidades comunes.

## Ejecución

```bash
# Instalar
pip install bandit

# Analizar todo el proyecto
bandit -r . -c pyproject.toml

# Con formato HTML
bandit -r . -f html -o bandit-report.html

# Solo severidad alta y media
bandit -r . -lll
```

## Configuración (`pyproject.toml`)

```toml
[tool.bandit]
exclude_dirs = ["migrations", "tests", ".venv", "site", "node_modules"]
skips = ["B101"]  # permitir assert en tests
```

## Hallazgos Comunes

| ID | Descripción | Estado |
|----|-------------|--------|
| B101 | Uso de `assert` (permitido en tests) | Skipped |
| B110 | `except:` sin excepción específica | En revisión |
| B311 | Uso de `random` (no criptográfico) | Aceptado (solo para tests) |

## Reportes

Los reportes de Bandit se generan automáticamente en el pipeline de Jenkins y se envían a SonarQube.
