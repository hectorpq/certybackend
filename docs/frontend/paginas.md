# Páginas del Frontend — `src/pages/`

## `auth/LoginPage.tsx`

Formulario de inicio de sesión con email y contraseña. Integración Google OAuth. Redirige a `/dashboard` tras login exitoso.

## `auth/RegisterPage.tsx`

Formulario de registro con email, nombre completo y contraseña (con confirmación).

## `dashboard/DashboardPage.tsx`

Panel principal con tarjetas de estadísticas (certificados, eventos, participantes, instructores) y accesos directos. Usa `useEvents` y `useCertificates`.

Detalles en [Dashboard](dashboard.md).

## `events/EventsPage.tsx`

Lista paginada de eventos con búsqueda y filtro por estado. Modal de creación/edición de eventos.

## `events/detail/EventDetailPage.tsx` (~840 líneas)

Página más compleja del frontend. Incluye:

- **Info del evento** — Datos generales y estado
- **Gestión de participantes** — Lista de inscritos con toggle de asistencia
- **Certificados** — Generar y enviar certificados por lote
- **Invitaciones** — Enviar invitaciones por email
- **Estadísticas** — Gráficos y métricas del evento
- **Configuración visual** — Posición del nombre en el certificado

## `participants/StudentsPage.tsx`

Lista paginada de participantes con búsqueda. CRUD mediante modal. Botón de importación Excel.

## `instructors/InstructorsPage.tsx`

Lista de instructores. CRUD modal con campos de firma digital.

## `certificates/CertificatesPage.tsx`

Lista paginada de certificados con búsqueda y filtro por estado/evento. Vista de detalle con historial de entregas. Acciones: generar PDF, enviar por email/whatsapp/link, reintentar.

## `templates/TemplatesPage.tsx` (~514 líneas)

CRUD de plantillas con canvas interactivo para posicionar el nombre del participante sobre la imagen de fondo. Subida de imagen de fondo y firma digital.

## `bulk/BulkGeneratePage.tsx`

Asistente de 4 pasos para generación masiva. Detalles en [Carga Masiva](bulk.md).

## `invitation/InvitationPage.tsx` (~262 líneas)

Página pública para aceptar invitaciones a eventos mediante token. Muestra detalles del evento. Permite registro de nuevo usuario si el invitado no existe en el sistema.
