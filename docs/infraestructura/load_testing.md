# Pruebas de Carga con Locust — `locust/locustfile.py`

## Escenarios de Carga

Tres clases de usuario simulando diferentes perfiles de uso:

### `PublicUser` (peso: 3)

Usuarios anónimos simulando tráfico público:

| Tarea | Peso | Endpoint |
|-------|------|----------|
| Verificar certificado | 10 | `GET /api/certificates/verify/?code=XXXX` |
| Obtener OpenAPI Schema | 3 | `GET /api/schema/` |
| Acceder a Swagger UI | 1 | `GET /api/docs/` |

### `CoordinatorUser` (peso: 2)

Usuarios autenticados como coordinadores realizando operaciones diarias. Se autentica al iniciar con `POST /api/login/` y reutiliza el token JWT.

| Tarea | Peso | Endpoint |
|-------|------|----------|
| Listar eventos | 5 | `GET /api/events/` |
| Listar participantes | 5 | `GET /api/participants/` |
| Listar certificados | 4 | `GET /api/certificates/` |
| Listar certificados página 2 | 2 | `GET /api/certificates/?page=2` |
| Listar entregas | 1 | `GET /api/deliveries/` |
| Listar auditoría | 1 | `GET /api/audit/` |

### `AdminUser` (peso: 1)

Usuarios admin realizando operaciones pesadas. Autenticación similar al coordinador.

| Tarea | Peso | Endpoint |
|-------|------|----------|
| Listar eventos | 3 | `GET /api/events/` |
| Listar certificados | 2 | `GET /api/certificates/` |
| Exportar certificados CSV | 1 | `GET /api/certificates/export/?file_format=csv` |
| Listar instructores | 1 | `GET /api/instructors/` |

## Cómo Ejecutar

```bash
# Instalar Locust
pip install locust

# Iniciar pruebas (web UI en http://localhost:8089)
locust -f locust/locustfile.py --host=http://localhost:8000

# Modo headless (sin UI, 100 usuarios, 10/s rate)
locust -f locust/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 --run-time 5m

# Con etiquetas específicas
locust -f locust/locustfile.py --host=http://localhost:8000 --tags public
```

## Variables de Entorno

| Variable | Default | Propósito |
|----------|---------|-----------|
| `LOCUST_COORD_EMAIL` | `perf_coordinator@test.local` | Email del coordinador de prueba |
| `LOCUST_COORD_PASSWORD` | `PerfPass123!` | Contraseña del coordinador |
| `LOCUST_ADMIN_EMAIL` | `perf_admin@test.local` | Email del admin de prueba |
| `LOCUST_ADMIN_PASSWORD` | `PerfAdmin123!` | Contraseña del admin |
