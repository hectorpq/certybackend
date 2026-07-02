# Matriz de Trazabilidad Requisitos ↔ Código

## RF → Endpoints

| Requisito | Endpoint(s) | Módulo |
|-----------|-------------|--------|
| RF-01 Registro | `POST /api/register/` | `api/views.py → RegisterView` |
| RF-02 Login | `POST /api/login/` | `api/views.py → LoginView` |
| RF-03 Google OAuth | `POST /api/auth/google/` | `api/views.py → GoogleAuthView` |
| RF-04 JWT | Configuración en `settings.py` (SimpleJWT) | `config/settings.py` |
| RF-06 Logout | Cliente: Interceptor Axios + limpieza localStorage | `certyfront/src/services/api.ts` |
| RF-10 CRUD Eventos | `GET/POST/PATCH/DELETE /api/events/` | `api/views.py → EventsViewSet` |
| RF-11 Estados Evento | Campo `status` en modelo Event | `events/models.py` |
| RF-13 Inscribir individual | `POST /api/events/{id}/enroll/` | `api/views.py → EventsViewSet.enroll` |
| RF-14 Inscribir masivo | `POST /api/events/{id}/invitations/send/` + Excel | `api/views.py` + `procesos/services.py` |
| RF-16 Generar certificados lote | `POST /api/events/{id}/certificates/generate/` | `api/views.py` |
| RF-17 Enviar certificados lote | `POST /api/events/{id}/certificates/send/` | `api/views.py` |
| RF-20 PDF personalizado | `POST /api/certificates/{id}/generate/` + `PDFService` | `services/pdf_service.py` |
| RF-21 Código QR | `PDFService._draw_qr_code()` | `services/pdf_service.py` |
| RF-24 Verificación | `GET /api/certificates/verify/?code=XXXX` | `api/views.py → CertificateViewSet.verify` |
| RF-25 Historial entregas | `GET /api/certificates/{id}/history/` | `api/views.py` + `DeliveryLog` |
| RF-30 CRUD Participantes | `GET/POST/PATCH/DELETE /api/participants/` | `api/views.py → ParticipantsViewSet` |
| RF-31 Importar Excel | `POST /api/participants/import_participants/` | `api/views.py` + `procesos/services.py` |
| RF-35 CRUD Plantillas | `GET/POST/PUT/PATCH/DELETE /api/templates/` | `api/views.py → TemplateViewSet` |
| RF-40 AuditLog generación | `log_action("certificate_generated", ...)` en views | `api/audit.py` |

## HU → Componentes Frontend

| Historia | Componente | Ruta |
|----------|------------|------|
| HU-01 Gestionar usuarios | Vía admin de Django (no implementado en frontend) | — |
| HU-02 Ver auditoría | Sin página dedicada; endpoint `GET /api/audit/` | — |
| HU-10 Crear evento | `EventsPage.tsx` + Modal de creación | `/events` |
| HU-11 Cargar Excel | `BulkGeneratePage.tsx` (paso 1-2) | `/bulk-generate` |
| HU-12 Diseñar plantilla | `TemplatesPage.tsx` (canvas interactivo) | `/templates` |
| HU-13 Generar lotes | `EventDetailPage.tsx` (botón generar) | `/events/:id` |
| HU-14 Enviar lotes | `EventDetailPage.tsx` (botón enviar) | `/events/:id` |
| HU-15 Asistencia | `EventDetailPage.tsx` (toggle asistencia) | `/events/:id` |
| HU-20 Ver certificados | `CertificatesPage.tsx` | `/certificates` |
| HU-21 Verificar | Página pública (verificación) | `/verify?code=XXXX` |

## HU → Tests

| Historia | Test E2E | Archivo |
|----------|----------|---------|
| HU-10 Crear evento | `Crear evento con datos válidos` | `e2e/events.spec.ts` |
| HU-11 Cargar Excel | `Tab Por Excel muestra formulario` | `e2e/bulk.spec.ts` |
| HU-20 Ver certificados | `Listar certificados` | `e2e/certificates.spec.ts` |
| HU-21 Verificar | `Página de verificación pública carga` | `e2e/certificates.spec.ts` |
| Login | `Login exitoso redirige al dashboard` | `e2e/auth.spec.ts` |
