# Dashboard — `DashboardPage.tsx`

## Estructura General

El Dashboard es la página principal después del inicio de sesión. Muestra un resumen visual del estado del sistema mediante tarjetas de estadísticas y accesos directos a las funcionalidades principales.

## Tarjetas Informativas

Cada tarjeta representa una métrica clave del sistema, obtenida de los respectivos endpoints de la API:

- **Certificados** — Total de certificados emitidos en el sistema (desde `/api/certificates/`).
- **Eventos** — Total de eventos registrados (desde `/api/events/`).
- **Participantes** — Total de participantes registrados (desde `/api/participants/`).
- **Instructores** — Total de instructores registrados (desde `/api/instructors/`).

## Accesos Directos

El Dashboard incluye enlaces rápidos (botones grandes) para navegar a las secciones principales:

- **Ir a Certificados** → `/certificates`
- **Ir a Eventos** → `/events`
- **Ir a Participantes** → `/participants`
- **Generar Certificados** → `/bulk-generate`

Para usuarios con rol `participante`, el Dashboard muestra únicamente los datos relevantes a su perfil (sus certificados y eventos donde está inscrito).

## Hooks de Estado

### `useCertificates.ts`

Hook que utiliza `@tanstack/react-query` para gestionar el estado de certificados:

- `useCertificates(filters)` — Query para lista paginada de certificados
- `useCertificate(id)` — Query para detalle de un certificado
- `useGenerateCertificate()` — Mutación para generar PDF
- `useDeliverCertificate()` — Mutación para entregar certificado
- `useRetryDelivery()` — Mutación para reintentar entrega

### `useEvents.ts`

Hook para gestión de eventos:

- `useEvents(filters)` — Query para lista paginada de eventos
- `useEvent(id)` — Query para detalle de evento
- `useCreateEvent()` — Mutación para crear evento
- `useUpdateEvent()` — Mutación para actualizar evento
- `useDeleteEvent()` — Mutación para eliminar evento
- `useEventParticipants(id)` — Query para participantes de un evento
- `useEventStats(id)` — Query para estadísticas de un evento
- `useEventGenerateCertificates()` — Mutación para generar certificados de evento
- `useEventDeliverCertificates()` — Mutación para enviar certificados de evento
