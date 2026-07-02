# Pruebas de Carga (Locust)

## Escenarios

Tres clases de usuario simulando diferentes perfiles de uso:

### `PublicUser` (peso 3)
- Verificación de certificados (10x)
- Schema OpenAPI (3x)
- Swagger UI (1x)

### `CoordinatorUser` (peso 2)
- Listar eventos (5x), participantes (5x), certificados (4x + 2x paginación)
- Listar entregas (1x), auditoría (1x)

### `AdminUser` (peso 1)
- Listar eventos (3x), certificados (2x)
- Exportar CSV (1x), instructores (1x)

## Ejecución

```bash
# Instalar
pip install locust

# UI web (http://localhost:8089)
locust -f locust/locustfile.py --host=http://localhost:8000

# Headless: 100 usuarios, 10/s rate, 5 minutos
locust -f locust/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 --run-time 5m

# Solo escenario público
locust -f locust/locustfile.py --host=http://localhost:8000 --tags public
```

## Variables de Entorno

| Variable | Default | Propósito |
|----------|---------|-----------|
| `LOCUST_COORD_EMAIL` | `perf_coordinator@test.local` | Email coordinador |
| `LOCUST_COORD_PASSWORD` | `PerfPass123!` | Password coordinador |
| `LOCUST_ADMIN_EMAIL` | `perf_admin@test.local` | Email admin |
| `LOCUST_ADMIN_PASSWORD` | `PerfAdmin123!` | Password admin |

## Métricas Clave

- **Tiempo de respuesta** (p95 < 500ms para CRUD)
- **Tasa de error** (< 1%)
- **RPS** (requests per second) sostenido
- **Usuarios concurrentes** sin degradación
