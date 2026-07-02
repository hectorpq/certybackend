# Pruebas Unitarias

## Backend (pytest)

Los tests del backend se encuentran en cada app de Django:

```
certybackend/
├── api/tests.py
├── certificados/tests.py
├── events/tests.py
├── ...
└── pytest.ini
```

### Configuración

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
pythonpath = .
testpaths = api certificados events participants users instructors deliveries services procesos
```

### Ejecución

```bash
# Todas las pruebas
pytest

# Con cobertura
pytest --cov=. --cov-report=term-missing

# App específica
pytest certificados/tests.py

# Test específico
pytest certificados/tests.py::test_generar_certificado
```

### Buenas Prácticas

- Usar `pytest-django` con `db` fixture para pruebas que requieren BD
- Usar `django.test.Client` o DRF `APIClient` para probar endpoints
- Usar `mock` o `responses` para servicios externos (SendGrid, WhatsApp)
- Factory Boy para crear datos de prueba

## Frontend (Vitest)

Los tests del frontend están en `certyfront/src/test/`:

```bash
cd certyfront
npm run test          # Una vez
npm run test:watch    # Modo watch
npm run test:coverage # Con reporte de cobertura
```

### Stack

- **Vitest** — Test runner
- **@testing-library/react** — Renderizado y eventos de componentes
- **msw** (Mock Service Worker) — Mock de APIs
