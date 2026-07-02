# Cobertura de Código

## Backend — pytest-cov

```bash
# Generar reporte
pytest --cov=. --cov-report=term-missing --cov-report=xml

# Reporte XML (para SonarQube)
# → coverage.xml

# Solo apps específicas
pytest --cov=api --cov=certificados --cov=events --cov=participants
```

### Configuración

- Archivo: `.coveragerc` (omitir migrations, admin.py, apps.py, config/)
- Integración con SonarQube via `coverage.xml`
- Ejecutado automáticamente en pipeline Jenkins

## Frontend — Vitest + @vitest/coverage-v8

```bash
npm run test:coverage
# → coverage/lcov.info (para SonarQube)
```

### Configuración

En `vite.config.ts`:
```typescript
test: {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'lcov'],
    include: ['src/**/*.{ts,tsx}'],
    exclude: ['src/test/**', '**/*.test.*', 'src/vite-env.d.ts']
  }
}
```

## Umbrales

| Nivel | Mínimo |
|-------|--------|
| Líneas de código | 80% |
| Ramas (branches) | 70% |
| Funciones | 80% |

## Reportes

- **Terminal:** `pytest --cov --cov-report=term-missing`
- **HTML:** `pytest --cov --cov-report=html` → `htmlcov/index.html`
- **SonarQube:** Via `coverage.xml` (backend) y `lcov.info` (frontend)
