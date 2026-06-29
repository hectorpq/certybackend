# CI/CD con Jenkins

## Backend — `certybackend/Jenkinsfile`

Pipeline declarativo con 4 etapas:

### Etapa 1: Limpieza y Entorno

- Genera archivo `.env` con credenciales de prueba para la base de datos PostgreSQL
- Limpia contenedores previos (`docker rm -f test_runner`)

### Etapa 2: Build Infrastructure

- Construye las imágenes Docker: `web`, `db`, `redis`
- `docker-compose -p certybackend build --no-cache web`

### Etapa 3: Test & Coverage

- Ejecuta `pytest --reuse-db --cov=. --cov-report=xml` dentro del contenedor `web`
- Extrae el archivo `coverage.xml` del contenedor

### Etapa 4: Static Analysis (SonarQube)

- Ejecuta `sonar-scanner` con el token de SonarQube y la ruta de cobertura
- Usa `SonarQubeServer` como servidor configurado en Jenkins

### Post

- Limpieza del contenedor `test_runner`

## Frontend — `certyfront/Jenkinsfile`

Pipeline declarativo con 2 etapas:

### Etapa 1: Pipeline Frontend

- Corre dentro de `node:20-slim`
- `npm install`
- `npm run test` (unitarias con cobertura)
- `npm run build`

### Etapa 2: Static Analysis (SonarQube)

- Ejecuta `sonar-scanner` contra `SonarQubeServer`

## Cómo Ejecutar Localmente

```bash
# Backend
docker-compose -p certybackend build web
docker-compose -p certybackend run --name test_runner web pytest --reuse-db --cov=. --cov-report=xml
docker cp test_runner:/app/coverage.xml ./coverage.xml
docker rm -f test_runner

# Frontend
docker run --rm -v ${PWD}:/app -w /app node:20-slim sh -c "npm install && npm run test && npm run build"
```
