# Pruebas E2E con Playwright

## Configuración

Las pruebas End-to-End se encuentran en `certyfront/e2e/` y están configuradas en `playwright.config.ts`.

- **Navegador:** Chromium (solo)
- **URL base:** `http://localhost:5173` (servidor de desarrollo de Vite)
- **Timeout:** 30 segundos por prueba
- **Capturas:** Solo en fallo
- **Traza:** Retenida en fallo
- **Reintentos:** 1 por prueba fallida

## Suite de Pruebas

### `auth.spec.ts` — Autenticación

| Prueba | Descripción |
|--------|-------------|
| Login exitoso redirige al dashboard | Verifica que con credenciales válidas se redirige a `/dashboard` y se muestra "Panel" |
| Login con contraseña incorrecta muestra error | Verifica que credenciales inválidas muestran mensaje de error |
| Login con campos vacíos muestra validación | Verifica que el formulario vacío no redirige |
| Acceso a `/dashboard` sin autenticación | Verifica redirección a `/login` |
| Acceso a `/events` sin autenticación | Verifica redirección a `/login` |
| Acceso a `/bulk-generate` sin autenticación | Verifica redirección a `/login` |

**Credenciales de prueba:** `admin@certypro.com` / `admin123`

### `bulk.spec.ts` — Generación Masiva

| Prueba | Descripción |
|--------|-------------|
| Página carga con tabs Por Evento / Por Excel | Verifica que ambos tabs existen |
| Tab Por Excel muestra formulario de carga | Verifica que se muestra "Subir" |
| Selector de evento en tab Por Evento | Verifica que hay opciones en el select |

### `certificates.spec.ts` — Certificados

| Prueba | Descripción |
|--------|-------------|
| Listar certificados | Verifica que la tabla de certificados carga y muestra un `<h1>` |
| Página de verificación pública carga | Verifica que `/verify?code=TEST-CODE` carga correctamente |
| Navegación a detalle de certificado | Verifica que al hacer clic en una fila se navega al detalle |

### `dashboard.spec.ts` — Dashboard

| Prueba | Descripción |
|--------|-------------|
| Dashboard carga con cards de estadísticas | Verifica que "Certificados" y "Eventos" son visibles |
| Navegación a Eventos | Verifica clic en enlace a `/events` |
| Navegación a Participantes | Verifica clic en enlace a `/participants` |
| Navegación a Certificados | Verifica clic en enlace a `/certificates` |
| Navegación a Generación Masiva | Verifica clic en enlace a `/bulk-generate` |

### `events.spec.ts` — Eventos

| Prueba | Descripción |
|--------|-------------|
| Listar eventos | Verifica que la página de eventos carga |
| Crear evento con datos válidos | Completa formulario con nombre, fecha, duración y ubicación; verifica que el evento aparece en la lista |
| Crear evento sin nombre muestra error | Verifica que el modal de creación sigue abierto si falta el nombre |

### `participants.spec.ts` — Participantes

| Prueba | Descripción |
|--------|-------------|
| Listar participantes | Verifica que la página carga |
| Crear participante con datos válidos | Completa formulario con documento, nombre, apellido y email; verifica que aparece en la lista |
| Buscar participante | Verifica que el campo de búsqueda funciona |

## Cómo Ejecutar las Pruebas

```bash
# 1. Asegurar que el servidor de desarrollo esté corriendo
cd certyfront && npm run dev

# 2. En otra terminal, ejecutar todas las pruebas
npx playwright test

# 3. Abrir interfaz gráfica
npx playwright test --ui

# 4. Ver reporte HTML
npx playwright show-report

# 5. Ejecutar un archivo específico
npx playwright test e2e/auth.spec.ts
```

!!! warning "Requisitos"
    - El backend de Django debe estar corriendo en `http://localhost:8000`
    - Debe existir un usuario admin con email `admin@certypro.com` y contraseña `admin123`
    - Ejecutar `npx playwright install` la primera vez para instalar los navegadores
