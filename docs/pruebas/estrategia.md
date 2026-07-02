# Estrategia de Pruebas

## Pirámide de Pruebas

```
        ╱╲
       ╱ E2E ╲            ← Playwright (flujos críticos)
      ╱────────╲
     ╱ Integración ╲      ← Django TestCase + DRF APIClient (API)
    ╱────────────────╲
   ╱   Unitarias        ╲  ← pytest / vitest (modelos, servicios, hooks)
  ╱────────────────────────╲
```

## Niveles

| Nivel | Herramienta | Cobertura | Qué se prueba |
|-------|-------------|-----------|---------------|
| **Unitarias** | pytest + vitest | ≥80% líneas | Modelos, servicios, utilidades, hooks |
| **Integración** | Django TestCase + DRF APIClient | — | Endpoints API, flujos CRUD, permisos |
| **E2E** | Playwright | Flujos críticos | Login, bulk, certificados, eventos, dashboard, participantes |

## Cobertura Mínima

- **Código nuevo:** ≥90% en líneas
- **Código existente:** Mantener o mejorar cobertura actual
- **Umbral de fallo:** <80% de cobertura general → pipeline falla

## Ejecución

```bash
# Backend: unitarias + integración
pytest --cov=. --cov-report=term-missing

# Frontend: unitarias
npm run test

# Frontend: E2E
npx playwright test
```
