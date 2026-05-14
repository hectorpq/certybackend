# Guía de Pruebas de Integración con Testcontainers - CertyPro Backend

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Configuración Inicial](#configuración-inicial)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Conceptos Principales](#conceptos-principales)
5. [Cómo Ejecutar las Pruebas](#cómo-ejecutar-las-pruebas)
6. [Ejemplos de Pruebas](#ejemplos-de-pruebas)
7. [Integración con SonarQube](#integración-con-sonarqube)
8. [Solución de Problemas](#solución-de-problemas)

---

## Descripción General

Este proyecto implementa pruebas de **integración con Testcontainers**, utilizando una **base de datos PostgreSQL real en Docker** en lugar de bases de datos en memoria (H2, SQLite).

### ¿Por qué Testcontainers?

- ✅ **BD Real**: Las pruebas se ejecutan contra la misma BD que usaremos en producción
- ✅ **Aislamiento**: Cada sesión de pruebas tiene su propio contenedor independiente
- ✅ **Limpieza Automática**: Los contenedores se detienen y eliminan automáticamente
- ✅ **Reproducibilidad**: Las pruebas son deterministas y reproducibles
- ✅ **Compatibilidad**: Detecta problemas específicos de PostgreSQL

### Equivalencia con Spring Boot

| Aspecto | Spring Boot (Java) | Django (Python) |
|--------|-------------------|-----------------|
| **Gestión de Contenedores** | `@Testcontainers` | `conftest.py` (fixture session) |
| **Inyección Dinámica de Credenciales** | `@DynamicPropertySource` | `_override_django_database_settings()` |
| **Limpieza Previa a Tests** | `@BeforeEach` | `setup_method()` |
| **Test Framework** | `JUnit 5` | `pytest` |
| **BD de Pruebas** | `MySQLContainer` | `PostgresContainer` |
| **Pruebas Parametrizadas** | `@ParameterizedTest` + `@ValueSource` | `@pytest.mark.parametrize` |
| **Marcadores** | `@DataJpaTest` | `@pytest.mark.django_db` |

---

## Configuración Inicial

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Las dependencias principales son:

- **testcontainers[postgresql]==4.7.1**: Gestión de contenedores Docker
- **pytest==7.4.4**: Framework de pruebas
- **pytest-django==4.7.0**: Integración Django con pytest
- **pytest-cov==4.1.0**: Cobertura de código
- **factory-boy==3.3.0**: Generación de datos de prueba (opcional)

### 2. Verificar Requisitos

```bash
# Docker debe estar disponible
docker --version

# Python 3.8+
python --version

# Verificar que DATABASES está configurado correctamente en settings.py
```

### 3. Configuración de Django (settings.py)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT"),
    }
}
```

> **Nota**: En tiempo de pruebas, `conftest.py` sobrescribe automáticamente estos valores con las credenciales del contenedor.

---

## Estructura de Archivos

```
certybackend/
├── conftest.py                              # ← Fixture global de Testcontainers
├── pytest.ini                               # ← Configuración de pytest y cobertura
├── sonar-project.properties                 # ← Configuración de SonarQube
├── requirements.txt                         # ← Dependencias (con testcontainers)
│
├── events/
│   ├── models.py                           # Modelos de eventos
│   ├── tests.py                            # Pruebas unitarias existentes
│   └── test_db_integration.py              # ← Pruebas de integración (NUEVO)
│
├── config/
│   ├── settings.py                         # Configuración de Django
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
└── [otras aplicaciones...]
```

### Archivos Clave Creados/Modificados

| Archivo | Cambios |
|---------|---------|
| **conftest.py** | ✨ NUEVO - Gestión del contenedor PostgreSQL |
| **events/test_db_integration.py** | ✨ NUEVO - Suite de pruebas de integración |
| **pytest.ini** | 📝 Actualizado - Añadida configuración de cobertura |
| **sonar-project.properties** | 📝 Actualizado - Exclusiones para conftest.py |
| **requirements.txt** | 📝 Actualizado - Dependencias de Testcontainers |

---

## Conceptos Principales

### 1. Fixture `setup_postgres_container` (conftest.py)

```python
@pytest.fixture(scope='session', autouse=True)
def setup_postgres_container() -> Generator[dict, None, None]:
    """Gestiona el ciclo de vida del contenedor PostgreSQL"""
    container_manager = PostgreSQLTestContainer()
    credentials = container_manager.start()
    
    # Sobrescribir DATABASES de Django
    _override_django_database_settings(credentials)
    
    yield credentials
    
    # Limpieza: Detener el contenedor
    container_manager.stop()
```

**Alcance (scope)**: `'session'`
- Se ejecuta **una sola vez** al inicio de toda la sesión de pruebas
- Los datos se comparten entre todos los tests (es responsabilidad de cada test limpiar si es necesario)
- Más eficiente que crear un contenedor por cada test

### 2. Clase `PostgreSQLTestContainer`

Equivalente a la clase `MySQLTestContainer` del ejemplo Spring Boot.

```python
class PostgreSQLTestContainer:
    """Gestiona el contenedor Docker de PostgreSQL"""
    
    def start(self) -> dict:
        """Inicia el contenedor y retorna credenciales"""
        self.container = PostgresContainer(
            image="postgres:16-alpine",
            dbname="testdb",
            username="testuser",
            password="testpass",
        )
        self.container.start()
        return {
            'url': self.container.get_connection_url(),
            'user': self.container.username,
            'password': self.container.password,
            'db_name': self.container.dbname,
            'host': self.container.get_container_host_ip(),
            'port': self.container.get_exposed_port('5432'),
        }
    
    def stop(self):
        """Detiene y elimina el contenedor"""
        self.container.stop()
```

### 3. Anotaciones en Tests

#### `@pytest.mark.django_db`

Habilita acceso a la base de datos para el test.

```python
@pytest.mark.django_db
def test_event_creation():
    event = Event.objects.create(name="Python Workshop")
    assert event.id is not None
```

Equivalente a `@DataJpaTest` en Spring Boot.

#### `@pytest.mark.integration`

Marca explícitamente un test como prueba de integración.

```python
@pytest.mark.integration
class TestEventRepositoryIntegration:
    """Suite de pruebas de integración"""
    pass
```

Permite ejecutar solo pruebas de integración:
```bash
pytest -m integration
```

#### `@pytest.mark.parametrize`

Ejecuta un test múltiples veces con diferentes parámetros.

```python
@pytest.mark.parametrize(
    "event_name,status,capacity",
    [
        ("Django Mastery", "active", 30),
        ("FastAPI Workshop", "draft", 25),
        ("GraphQL Tutorial", "active", 40),
    ]
)
def test_save_event_with_different_values(event_name, status, capacity):
    """Se ejecuta 3 veces, una por cada tupla de parámetros"""
    event = Event.objects.create(
        name=event_name,
        status=status,
        max_capacity=capacity
    )
    assert event.name == event_name
```

Equivalente a `@ParameterizedTest` + `@ValueSource`/`@CsvSource` en Spring Boot.

---

## Cómo Ejecutar las Pruebas

### Ejecutar Todas las Pruebas

```bash
pytest
```

**Salida esperada:**
```
===================== test session starts ======================
platform linux -- Python 3.11.0
collected 23 items

conftest.py::setup_postgres_container PASSED            [ 0%]
events/test_db_integration.py::TestEventRepositoryIntegration::test_save_event_persists_and_assigns_id PASSED [ 4%]
events/test_db_integration.py::TestEventRepositoryIntegration::test_save_event_with_different_names_and_status[django-event] PASSED [ 8%]
...
===================== 23 passed in 8.45s ======================
```

### Ejecutar Solo Pruebas de Integración

```bash
pytest -m integration
```

### Ejecutar Solo Pruebas Unitarias

```bash
pytest -m unit
```

### Ejecutar un Test Específico

```bash
# Por nombre exacto
pytest events/test_db_integration.py::TestEventRepositoryIntegration::test_save_event_persists_and_assigns_id

# Por patrón
pytest events/test_db_integration.py -k "save_event"
```

### Ejecutar con Cobertura Detallada

```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
```

**Genera:**
- `coverage.xml` - Formato XML para SonarQube
- `htmlcov/index.html` - Reporte HTML interactivo

### Ejecutar con Salida Verbose

```bash
pytest -v --tb=short
```

### Ejecutar Siguiendo un Orden Específico

```bash
pytest events/test_db_integration.py -v --collect-only
```

---

## Ejemplos de Pruebas

### Ejemplo 1: Crear y Persistir Datos

```python
@pytest.mark.django_db
def test_save_event_persists_and_assigns_id(self, create_test_event):
    """
    Prueba que el evento se guarda en la BD real y se asigna un ID.
    
    Equivalente a:
    testGuardarCategoria_PersisteCategoriaConIdGenerado() (Spring Boot)
    """
    assert create_test_event.id is not None
    assert create_test_event.id > 0
    assert create_test_event.name == "Python Workshop"
```

### Ejemplo 2: Prueba Parametrizada

```python
@pytest.mark.parametrize(
    "event_name,status,capacity",
    [
        ("Django Mastery", "active", 30),
        ("FastAPI Workshop", "draft", 25),
    ]
)
def test_save_with_different_values(event_name, status, capacity):
    """
    Se ejecuta 2 veces, probando diferentes combinaciones.
    
    Equivalente a:
    @ParameterizedTest + @CsvSource (Spring Boot)
    """
    event = Event.objects.create(
        name=event_name,
        status=status,
        max_capacity=capacity
    )
    assert event.name == event_name
    assert event.status == status
```

### Ejemplo 3: Pruebas de Búsqueda y Filtrado

```python
@pytest.mark.django_db
def test_find_events_by_status_returns_filtered_results(self):
    """Verifica que el filtrado por estatus funciona en BD real"""
    
    # Crear eventos con diferentes estatus
    for status in ["active", "draft", "finished"]:
        Event.objects.create(
            name=f"Event {status}",
            event_date=timezone.now().date(),
            status=status,
        )
    
    # Filtrar
    active_events = Event.objects.filter(status="active")
    
    # Verificar
    assert active_events.count() >= 1
    assert all(e.status == "active" for e in active_events)
```

### Ejemplo 4: Pruebas de Relaciones

```python
@pytest.mark.django_db
def test_event_relationships_with_foreign_keys(self):
    """Verifica que las relaciones se mantienen en BD real"""
    
    event = Event.objects.get(id=1)
    
    # Acceder a relaciones
    assert event.created_by.id == 1
    assert event.category.name == "Technology"
```

---

## Integración con SonarQube

### 1. Configuración Automática

El archivo `sonar-project.properties` ya está configurado para:

- **Fuente de cobertura**: `coverage.xml` (generado por pytest-cov)
- **Exclusiones**: Archivos de test, migraciones, admin.py
- **Versión Python**: 3.11

### 2. Generar Reporte de Cobertura

```bash
# Ejecutar pruebas con cobertura
pytest --cov=. --cov-report=xml:coverage.xml

# Resultado:
# ✓ coverage.xml creado
```

### 3. Enviar a SonarQube Cloud

```bash
# Instalar SonarQube CLI
# https://docs.sonarqube.org/latest/setup/cli/

# Ejecutar análisis
sonar-scanner \
  -Dsonar.projectKey=hectorpq_certybackend \
  -Dsonar.sources=. \
  -Dsonar.host.url=https://sonarcloud.io \
  -Dsonar.login=<YOUR_TOKEN>
```

### 4. Métricas de Cobertura

SonarQube mostrará:
- **Cobertura de Líneas**: % de líneas ejecutadas
- **Cobertura de Ramas**: % de bifurcaciones cubiertas
- **Complejidad Ciclomática**: Complejidad del código
- **Deuda Técnica**: Esfuerzo de refactoring

---

## Solución de Problemas

### Error: "Docker daemon is not running"

```
ERROR: Could not connect to Docker daemon
```

**Solución:**

```bash
# En Windows (Docker Desktop)
# Inicia Docker Desktop desde el menú de inicio

# En Linux
sudo systemctl start docker

# Verificar conexión
docker ps
```

### Error: "Connection refused" al conectar con PostgreSQL

```
psycopg2.OperationalError: could not connect to server
```

**Posibles causas:**
- Firewall bloqueando conexión
- Puerto ocupado
- Contenedor no inició correctamente

**Soluciones:**

```bash
# Ver logs del contenedor
docker logs $(docker ps -q)

# Listar contenedores en ejecución
docker ps -a

# Limpiar contenedores
docker container prune
```

### Error: "ModuleNotFoundError: No module named 'testcontainers'"

```
ModuleNotFoundError: No module named 'testcontainers'
```

**Solución:**

```bash
# Instalar dependencias nuevamente
pip install -r requirements.txt --force-reinstall

# O específicamente
pip install testcontainers[postgresql]==4.7.1
```

### Error: "DJANGO_DB_NAME already exists"

```
ProgrammingError: database "testdb" already exists
```

**Causa**: Restos de contenedores anteriores

**Solución:**

```bash
# Limpiar contenedores
docker rm -f $(docker ps -a -q)

# O simplemente cambiar el nombre de DB en conftest.py
```

### Pruebas Lentas o Timeout

```bash
# Aumentar timeout global
pytest --timeout=300

# O en pytest.ini
timeout = 300
```

### Conflicto con BD de Desarrollo

```bash
# Asegúrate de que settings.py usa variables de entorno
# La BD de pruebas sobrescribe automáticamente estas variables
```

---

## Mejores Prácticas

### ✅ DO's (Haz esto)

1. **Usa fixtures para datos de prueba**
   ```python
   @pytest.fixture
   def create_test_event():
       return Event.objects.create(...)
   ```

2. **Aíslate con transacciones**
   ```python
   @pytest.mark.django_db
   def test_something():
       # Cada test ejecuta en una transacción aislada
   ```

3. **Prueba un concepto por test**
   ```python
   def test_save_event_persists_id():  # ✓ Específico
       # vs
   def test_event():  # ✗ Demasiado genérico
   ```

4. **Usa nombres descriptivos**
   ```python
   def test_save_event_with_invalid_date_raises_error():  # ✓
   def test_save():  # ✗
   ```

5. **Parametriza casos similares**
   ```python
   @pytest.mark.parametrize("status", ["active", "draft"])
   def test_event_status(status):
       # En lugar de 2 tests separados
   ```

### ❌ DON'Ts (Evita esto)

1. **No depures en las pruebas**
   ```python
   # ✗ Malo
   print(event)
   # ✓ Bueno - Usa logging o breakpoints
   logger.info(f"Event: {event}")
   ```

2. **No crees órdenes de dependencia entre tests**
   ```python
   # ✗ Malo
   def test_1_create():
       ...
   def test_2_find():  # Depende de test_1
       ...
   # ✓ Bueno - Cada test es independiente
   ```

3. **No uses BD global sin limpieza**
   ```python
   # ✗ Malo
   Event.objects.all().delete()  # Al final, no siempre se ejecuta
   # ✓ Bueno - Confía en transacciones automáticas
   ```

---

## Referencias

- [Documentación Testcontainers Python](https://testcontainers.org/)
- [Documentación Pytest](https://docs.pytest.org/)
- [Documentación Pytest-Django](https://pytest-django.readthedocs.io/)
- [Django Testing Documentation](https://docs.djangoproject.com/en/5.2/topics/testing/)
- [SonarQube Python Analysis](https://docs.sonarqube.org/latest/analysis/languages/python/)

---

## Contacto y Soporte

Para preguntas o problemas, consulta:
- 📖 [CLAUDE.md](./CLAUDE.md) - Notas del proyecto
- 🐛 Issues en GitHub
- 📧 Contact the development team

---

**Última actualización**: Mayo 2026
**Versión**: 1.0
**Autor**: CertyPro Development Team
