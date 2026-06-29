# Módulo: Certificados

El módulo de `certificados` es el núcleo del sistema. Gestiona la creación, el ciclo de vida, la generación de PDF y la entrega de los certificados.

## Modelo de Datos: `Certificate`

El modelo `Certificate` almacena toda la información de un certificado.

- **`participant`**: Relación con el participante que recibe el certificado.
- **`event`**: Relación con el evento al que pertenece el certificado.
- **`template`**: Plantilla de diseño utilizada.
- **`status`**: Estado del ciclo de vida del certificado.
  - `pending`: Creado, pero el PDF no ha sido generado.
  - `generated`: El PDF ha sido generado y está listo para ser enviado.
  - `sent`: Entregado exitosamente al menos una vez.
  - `failed`: El último intento de entrega falló.
- **`verification_code`**: Código único para la verificación pública.
- **`pdf_url`**: Ruta al archivo PDF generado.
- **`expires_at`**: Fecha de vencimiento del certificado.

## Endpoints de la API

La gestión de certificados se realiza a través de `CertificateViewSet`.

### `GET /api/certificates/`
- **Descripción**: Lista todos los certificados. Los administradores ven todos; los participantes solo ven los suyos.
- **Permisos**: Autenticado.

### `POST /api/certificates/`
- **Descripción**: Crea un nuevo certificado manualmente. Requiere `participant_id`, `event_id` y `template_id`.
- **Permisos**: Administrador/Coordinador.

### `GET /api/certificates/{id}/`
- **Descripción**: Obtiene los detalles completos de un certificado, incluyendo su historial de entregas.
- **Permisos**: Autenticado (propietario) o Administrador.

### `POST /api/certificates/{id}/generate/`
- **Descripción**: Genera el archivo PDF del certificado. El estado cambia de `pending` a `generated`.
- **Permisos**: Administrador/Coordinador.

### `POST /api/certificates/{id}/deliver/`
- **Descripción**: Envía el certificado a través de un método específico (`email`, `whatsapp`, `link`).
- **Permisos**: Administrador/Coordinador.

### `GET /api/certificates/verify/?code={code}`
- **Descripción**: Endpoint público para verificar la autenticidad de un certificado usando su código.
- **Permisos**: Público (sin autenticación).

### `POST /api/certificates/generate-bulk/`
- **Descripción**: Endpoint para la carga masiva de certificados desde un archivo Excel.
- **Funcionamiento**:
  1. Recibe un archivo `excel_file`, una `template_image` y un `event_id`.
  2. Crea una plantilla temporal (`ad-hoc`) para este proceso.
  3. Utiliza `ExcelProcessingService` para leer el archivo, validar datos, crear/actualizar participantes, inscribirlos y generar los certificados.
  4. Cada certificado se genera y se intenta enviar por email en una transacción atómica por fila.
- **Permisos**: Administrador/Coordinador.

### `POST /api/certificates/preview/`
- **Descripción**: Permite previsualizar los datos de un archivo Excel sin procesarlos.
- **Funcionamiento**:
  1. Recibe un `excel_file`.
  2. `ExcelProcessingService` lee el archivo, valida las columnas y retorna los datos en formato JSON.
  3. El frontend puede usar estos datos para que el usuario los edite antes de enviarlos al endpoint de procesamiento final.
- **Permisos**: Administrador/Coordinador.

