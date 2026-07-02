# Documentación OpenAPI / Swagger

La API REST está documentada automáticamente mediante **drf-spectacular** (OpenAPI 3).

## Acceso a la Documentación

| Recurso | URL | Descripción |
|---------|-----|-------------|
| Swagger UI | `http://localhost:8000/api/docs/` | Interfaz interactiva para explorar y probar endpoints |
| OpenAPI Schema | `http://localhost:8000/api/schema/` | Schema JSON descargable (OpenAPI 3.0) |

## Generación del Schema

El schema se genera automáticamente desde los ViewSets y Serializers de DRF:

```yaml
# config/urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
```

## Configuración (settings.py)

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "Certy API",
    "DESCRIPTION": "Sistema de Gestión y Entrega Masiva de Certificados",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
```

## Uso en Desarrollo

```bash
# El schema se sirve automáticamente al iniciar el servidor
python manage.py runserver

# Abrir en navegador:
# http://localhost:8000/api/docs/  (Swagger UI)
# http://localhost:8000/api/schema/ (schema JSON)
```
