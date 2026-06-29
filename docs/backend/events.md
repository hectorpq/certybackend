# Módulo: Eventos

El módulo de `events` gestiona los cursos, talleres o cualquier actividad académica que culmine en la emisión de un certificado.

## Modelo de Datos: `Event`

El modelo `Event` define un evento académico.

- **`name`**: Nombre del evento (ej: "Curso de Python Avanzado").
- **`event_date`**: Fecha de realización del evento.
- **`instructor`**: Instructor que imparte el evento.
- **`template`**: Plantilla de certificado por defecto para este evento.
- **`status`**: Estado del evento (`draft`, `active`, `finished`, `cancelled`).

## Modelo de Datos: `Enrollment`

Representa la inscripción de un `Participant` a un `Event`.

- **`participant`**: El participante inscrito.
- **`event`**: El evento al que se inscribe.
- **`attendance`**: Booleano que indica si el participante asistió. **Es un requisito para generar el certificado.**
- **`created_by`**: Usuario que realizó la inscripción.

## Endpoints de la API

La gestión de eventos se realiza a través de `EventsViewSet`.

### `GET /api/events/`
- **Descripción**: Lista todos los eventos. Los administradores ven todos; los participantes solo ven aquellos en los que están inscritos.

### `POST /api/events/`
- **Descripción**: Crea un nuevo evento.

### `GET /api/events/{id}/`
- **Descripción**: Obtiene los detalles de un evento.

### `GET /api/events/{id}/participants/`
- **Descripción**: Lista todos los participantes inscritos en un evento, junto con el estado de su certificado.

### `POST /api/events/{id}/certificates/generate/`
- **Descripción**: Acción masiva para generar los certificados de todos los participantes que asistieron al evento.