# Análisis de Código con SonarQube

## Backend (`sonar-project.properties`)

```properties
sonar.projectKey=hectorpq_certybackend
sonar.projectName=CertyPro - Backend
sonar.language=py
sonar.python.version=3.11

sonar.sources=api, certificados, config, core, deliveries, events, instructors, participants, procesos, services, users

sonar.tests=api, certificados, core, deliveries, events, instructors, participants, procesos, services, users
sonar.test.inclusions=**/tests.py,**/test_*.py
sonar.exclusions=**/migrations/**,**/admin.py,**/apps.py,config/wsgi.py,config/asgi.py,manage.py,**/management/commands/**,services/whatsapp_service.py,test_student_api.py,certificados/views.py,core/views.py,deliveries/views.py,emails/views.py,events/views.py,instructors/views.py,procesos/views.py,students/views.py,users/views.py,participants/views.py,config/celery.py,config/settings.py
sonar.python.coverage.reportPaths=coverage.xml
```

**Fuentes analizadas:** `api`, `certificados`, `config`, `core`, `deliveries`, `events`, `instructors`, `participants`, `procesos`, `services`, `users`.

**Excluidos:** migraciones, administración de Django, configuración del proyecto y vistas vacías (archivos `views.py` que solo contienen comentarios).

## Frontend (`sonar-project.properties`)

```properties
sonar.projectKey=certy-frontend
sonar.projectName=certy-frontend
sonar.projectVersion=1.0

sonar.sources=src
sonar.tests=src
sonar.test.inclusions=src/**/*.test.ts,src/**/*.test.tsx

sonar.exclusions=node_modules/**,dist/**,build/**,.vite/**,src/vite-env.d.ts,**/*.stories.tsx
sonar.javascript.lcov.reportPaths=coverage/lcov.info
sonar.typescript.tsconfigPaths=tsconfig.sonar.json
```

## Cobertura de Código

### Backend

- **Herramienta:** `pytest-cov` con reporte en formato XML (`coverage.xml`).
- **Comando:** `pytest --cov --cov-report=xml`
- **Archivo de configuración:** `.coveragerc` y `pytest.ini`.

### Frontend

- **Herramienta:** `vitest` con `@vitest/coverage-v8`.
- **Comando:** `npm run test:coverage`
- **Reporte:** `coverage/lcov.info` (formato LCOV para SonarQube).
- **Archivo de configuración:** `vite.config.ts` sección `test.coverage`.

## Cómo Ejecutar el Análisis

```bash
# Backend
cd certybackend
pytest --cov --cov-report=xml
sonar-scanner

# Frontend
cd certyfront
npm run test:coverage
sonar-scanner
```

!!! hint "Métricas Clave"
    - **Cobertura mínima recomendada:** 80% en líneas de código
    - **Deuda técnica:** Se mantiene seguimiento en el reporte de SonarQube
    - **Code Smells:** Se revisan en cada análisis para mantener calidad
    - **Duplicación:** Configurada para excluir archivos de prueba
