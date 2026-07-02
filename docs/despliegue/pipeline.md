# Pipeline CI/CD (Jenkins)

## Backend — `certybackend/Jenkinsfile`

```groovy
pipeline {
    stages {
        stage('Limpieza y Entorno') {
            // Genera .env para pruebas, limpia contenedores
        }
        stage('Build Infrastructure') {
            // docker-compose build web, db, redis
        }
        stage('Test & Coverage') {
            // pytest --cov --cov-report=xml
        }
        stage('Static Analysis (SonarQube)') {
            // sonar-scanner con token + coverage
        }
    }
    post {
        always { /* limpiar contenedores */ }
    }
}
```

### Etapas en detalle

1. **Limpieza y Entorno** — Crea `.env` con credenciales de prueba; elimina contenedores previos
2. **Build Infrastructure** — Construye imágenes Docker sin caché
3. **Test & Coverage** — Ejecuta `pytest --reuse-db --cov=. --cov-report=xml` dentro del contenedor. Extrae `coverage.xml`
4. **Static Analysis** — Ejecuta SonarQube Scanner con token de autenticación

## Frontend — `certyfront/Jenkinsfile`

```groovy
pipeline {
    stages {
        stage('Pipeline Frontend') {
            // npm install, npm run test, npm run build
        }
        stage('Static Analysis (SonarQube)') {
            // sonar-scanner
        }
    }
}
```

### Etapas en detalle

1. **Frontend Pipeline** — Corre dentro de `node:20-slim`. Instala dependencias, ejecuta tests, compila build de producción
2. **SonarQube** — Análisis estático con configuración del proyecto

## Ejecución Manual

```bash
# Backend
cd certybackend
docker-compose build web
docker-compose run --name test_runner web pytest --reuse-db --cov=. --cov-report=xml
docker cp test_runner:/app/coverage.xml ./coverage.xml

# Frontend
cd certyfront
docker run --rm -v ${PWD}:/app -w /app node:20-slim sh -c "npm install && npm run test && npm run build"
```
