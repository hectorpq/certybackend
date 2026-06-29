# Módulo: Participantes

El módulo `participants` gestiona la información de los estudiantes o asistentes a los eventos.

## Modelo de Datos: `Participant`

El modelo `Participant` almacena los datos personales de cada individuo.

- **`document_id`**: Documento de identidad, debe ser único.
- **`first_name`**: Nombre(s) del participante.
- **`last_name`**: Apellido(s) del participante.
- **`email`**: Correo electrónico, debe ser único.
- **`phone`**: Número de teléfono, usado para entregas por WhatsApp.
- **`is_active`**: Booleano para activar o desactivar al participante.

## Endpoints de la API

La gestión de participantes se realiza a través de `ParticipantsViewSet`.

### `GET /api/participants/`
- **Descripción**: Lista todos los participantes registrados en el sistema. Soporta búsqueda y filtrado.

### `POST /api/participants/`
- **Descripción**: Crea un nuevo participante.

### `POST /api/participants/import_students/`
- **Descripción**: Permite importar masivamente participantes desde un archivo Excel o CSV. Si un `document_id` ya existe, la fila se omite para evitar duplicados.