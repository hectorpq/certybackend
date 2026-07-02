# Pruebas E2E (Playwright)

## Configuración

- **Navegador:** Chromium (solo)
- **URL base:** `http://localhost:5173` (Vite dev server)
- **Timeout:** 30s por test
- **Reintentos:** 1 por fallo
- **Traza y captura:** Solo en fallo

## Estructura — `certyfront/e2e/`

```
e2e/
├── auth.spec.ts             # Login, logout, redirecciones
├── bulk.spec.ts             # Carga masiva (tabs, formularios)
├── certificates.spec.ts     # Lista, detalle, verificación
├── dashboard.spec.ts        # Dashboard y navegación
├── events.spec.ts           # CRUD de eventos
└── participants.spec.ts     # CRUD de participantes
```

## Pruebas por Archivo

### `auth.spec.ts`
- Login exitoso redirige a dashboard
- Login con contraseña incorrecta muestra error
- Login con campos vacíos no redirige
- Acceso a rutas protegidas sin auth redirige a `/login`

### `bulk.spec.ts`
- Página carga con tabs Por Evento / Por Excel
- Tab Por Excel muestra formulario de subida
- Selector de evento en tab Por Evento

### `certificates.spec.ts`
- Lista de certificados carga
- Página de verificación pública funciona
- Navegación a detalle de certificado

### `dashboard.spec.ts`
- Dashboard carga con cards de estadísticas
- Navegación a Eventos, Participantes, Certificados, Bulk

### `events.spec.ts`
- Lista de eventos carga
- Crear evento con datos válidos
- Crear evento sin nombre muestra error

### `participants.spec.ts`
- Lista de participantes carga
- Crear participante con datos válidos
- Búsqueda de participante

## Ejecución

```bash
# Servidor de desarrollo (requerido)
cd certyfront && npm run dev

# En otra terminal
cd certyfront
npx playwright test           # Todos los tests
npx playwright test --ui      # UI interactiva
npx playwright test e2e/auth.spec.ts  # Archivo específico
npx playwright show-report    # Reporte HTML
```
