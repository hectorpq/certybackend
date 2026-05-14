# 🚀 Guía Rápida: Ejecutar Pruebas de Integración

## Requisitos Previos

- ✅ Docker instalado y en ejecución
- ✅ Python 3.8+
- ✅ Dependencias instaladas: `pip install -r requirements.txt`

---

## Comandos Principales

### 1. Ejecutar Todas las Pruebas

```bash
pytest
```

**Salida:**
```
============================== test session starts ==============================
collected 23 items

conftest.py::setup_postgres_container PASSED                            [  0%]
events/test_db_integration.py::TestEventRepositoryIntegration::test_save_event_persists_and_assigns_id PASSED [ 4%]
...
============================== 23 passed in 8.45s ==============================
```

### 2. Ejecutar Pruebas de Integración Solamente

```bash
pytest -m integration
```

### 3. Ejecutar Pruebas de una Aplicación Específica

```bash
pytest events/
```

### 4. Ejecutar un Test Específico

```bash
pytest events/test_db_integration.py::TestEventRepositoryIntegration::test_save_event_persists_and_assigns_id
```

### 5. Ejecutar Pruebas que Coincidan con un Patrón

```bash
pytest events/ -k "save_event"
```

### 6. Ejecutar con Reporte de Cobertura

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

**Genera:**
- `coverage.xml` → Para SonarQube
- `htmlcov/index.html` → Reporte HTML interactivo

### 7. Ejecutar en Modo Verbose

```bash
pytest -v
```

### 8. Ejecutar Parando en el Primer Error

```bash
pytest -x
```

### 9. Ejecutar Mostrando Outputs (print statements)

```bash
pytest -s
```

### 10. Ejecutar Mostrando Reporte Detallado

```bash
pytest -v --tb=long
```

---

## Secuencia de Ejecución (Qué Sucede)

```
1. pytest inicia
   ↓
2. conftest.py se carga
   ↓
3. PostgreSQLTestContainer.start() se ejecuta
   ├─ Descarga imagen postgres:16-alpine
   ├─ Inicia contenedor Docker
   ├─ Obtiene credenciales dinámicamente
   └─ Sobrescribe settings.DATABASES
   ↓
4. Primer test comienza
   ├─ @pytest.mark.django_db habilita acceso a BD
   ├─ Se ejecuta dentro de una transacción
   ├─ Los datos se persisten en PostgreSQL real
   └─ Al finalizar, la transacción se revierte (rollback)
   ↓
5. Siguiente test... (repite pasos 4)
   ↓
6. Todos los tests completados
   ↓
7. PostgreSQLTestContainer.stop() se ejecuta
   ├─ Detiene el contenedor
   ├─ Lo elimina
   └─ Libera recursos
   ↓
8. pytest termina
```

---

## Estructura de un Test

```python
import pytest
from events.models import Event

@pytest.mark.django_db          # ← Habilita acceso a BD
@pytest.mark.integration        # ← Marca como integración
class TestEventRepositoryIntegration:
    
    def test_save_event_persists_and_assigns_id(self, create_test_event):
        # Arrange (Preparar)
        # create_test_event es una fixture que proporciona un evento de prueba
        
        # Act (Actuar)
        # El evento ya está guardado por la fixture
        
        # Assert (Afirmar)
        assert create_test_event.id is not None
        assert create_test_event.name == "Python Workshop"
```

---

## Fixtures Disponibles

### Fixture 1: `create_test_user`

```python
def test_with_user(self, create_test_user):
    assert create_test_user.email == "testuser@example.com"
```

### Fixture 2: `create_test_category`

```python
def test_with_category(self, create_test_category):
    assert create_test_category.name == "Technology"
```

### Fixture 3: `create_test_event`

```python
def test_with_event(self, create_test_event):
    assert create_test_event.name == "Python Workshop"
    assert create_test_event.status == "active"
```

---

## Pruebas Parametrizadas

```python
@pytest.mark.parametrize(
    "event_name,status",
    [
        ("Django Mastery", "active"),
        ("FastAPI Workshop", "draft"),
        ("GraphQL Tutorial", "active"),
    ]
)
def test_multiple_events(event_name, status):
    event = Event.objects.create(
        name=event_name,
        status=status,
        event_date=timezone.now().date(),
    )
    assert event.name == event_name
    assert event.status == status
```

**Ejecución**: Se ejecuta 3 veces, una por cada tupla.

---

## Limpiar Datos Entre Tests

Django automáticamente revierte las transacciones después de cada test, pero puedes limpiar manualmente si es necesario:

```python
@pytest.mark.django_db
def test_with_manual_cleanup(self):
    Event.objects.all().delete()  # Limpiar eventos previos
    
    # Crear y probar
    event = Event.objects.create(name="Test")
    assert event.id is not None
```

---

## Enviar a SonarQube

### Paso 1: Generar Reporte de Cobertura

```bash
pytest --cov=. --cov-report=xml:coverage.xml
```

### Paso 2: Instalar SonarQube CLI

```bash
# macOS / Linux
brew install sonar-scanner

# Windows (descargar manualmente desde sonarqube.org)
```

### Paso 3: Ejecutar Análisis

```bash
sonar-scanner \
  -Dsonar.projectKey=hectorpq_certybackend \
  -Dsonar.organization=hectorpq11 \
  -Dsonar.sources=. \
  -Dsonar.host.url=https://sonarcloud.io \
  -Dsonar.login=<YOUR_SONARQUBE_TOKEN>
```

> Reemplaza `<YOUR_SONARQUBE_TOKEN>` con tu token de SonarQube

---

## Solución de Problemas Rápida

| Problema | Solución |
|----------|----------|
| **Docker not running** | Inicia Docker Desktop o `sudo systemctl start docker` |
| **Module not found** | `pip install -r requirements.txt` |
| **Port already in use** | `docker rm -f $(docker ps -q)` |
| **Slow tests** | `pytest --timeout=300` |
| **Want to see print statements** | `pytest -s` |
| **Database error** | `docker system prune -a` (limpia todo) |

---

## Configuración Avanzada

### Ejecutar Tests en Paralelo

```bash
pip install pytest-xdist
pytest -n auto
```

### Generar Reporte de Pruebas

```bash
pytest --html=report.html
```

### Ejecutar con Profiling

```bash
pytest --profile
```

### Ver Tests sin Ejecutarlos

```bash
pytest --collect-only
```

---

## Próximos Pasos

1. ✅ Lee [TESTING.md](./TESTING.md) para más detalles
2. 📖 Copia los ejemplos para tus propias pruebas
3. 🔄 Integra con CI/CD (GitHub Actions, GitLab CI, etc.)
4. 📊 Sube reportes a SonarQube
5. 🎯 Mantén cobertura > 80%

---

**¿Necesitas ayuda?** Consulta los archivos:
- `conftest.py` - Configuración global
- `events/test_db_integration.py` - Ejemplos de pruebas
- `TESTING.md` - Documentación completa
