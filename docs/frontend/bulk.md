# Carga Masiva (Bulk) — `BulkGeneratePage.tsx`

## Modos de Operación

La página de generación masiva soporta dos modos:

### Modo "Por Excel"

- **Paso 1 — Subir Excel:** El usuario selecciona un evento activo y sube un archivo Excel (`.xlsx`/`.xls`). El frontend valida que las columnas requeridas existan (`full_name`, `email`, `document_id`).
- **Paso 2 — Revisar:** El frontend muestra una tabla con los datos extraídos (hasta 20 filas visibles) para que el usuario verifique la información.
- **Paso 3 — Plantilla:** El usuario sube la imagen de fondo del certificado y configura interactivamente:
    - Posición del nombre (clic en la imagen para definir coordenadas X/Y en porcentaje)
    - Tamaño de fuente (slider de 12pt a 72pt)
    - Color del nombre (selector de color)
    - Firma digital del instructor (nombre, especialidad y archivo de firma)
- **Paso 4 — Resultado:** Muestra el resumen del procesamiento: total de registros, enviados exitosamente, fallidos y una lista detallada de errores.

### Modo "Por Evento"

- El usuario selecciona un evento existente y visualiza los participantes inscritos con su asistencia.
- Puede seleccionar participantes específicos o generar para todos los que asistieron.
- Configura la plantilla visual (imagen de fondo, posición del nombre, firma).
- Guarda la configuración en el evento (`PATCH /events/{id}/`) antes de generar.
- Los certificados se generan y envían en lote.

## Validación en el Cliente

Antes de enviar el archivo a la API, el frontend verifica:

- Que se haya seleccionado un evento
- Que el archivo Excel tenga las columnas requeridas
- Que la imagen de fondo esté en formato PNG o JPG
- Que los datos de la plantilla (posición, tamaño, color) sean válidos

## Llamadas a la API

- `POST /api/certificates/preview/` — Envía el Excel para previsualización (multipart: `excel_file`)
- `POST /api/certificates/generate-bulk/` — Envía el Excel + imagen de fondo + configuración para generar certificados (multipart: `excel_file`, `template_image`, `event_id`, `signature_image`, `name_x`, `name_y`, `font_size`, `font_color`)
- `POST /events/{id}/certificates/generate/` — Genera certificados para participantes de un evento
- `PATCH /events/{id}/` — Guarda configuración de plantilla en el evento

## Hooks Relacionados

### `useCertificates.ts`

- `usePreviewExcel()` — Mutación para previsualizar Excel
- `useGenerateBulkFull()` — Mutación para generación masiva completa

### `useEvents.ts`

- `useEvents({ status: 'active' })` — Obtiene eventos activos para el selector
- `useEvent(id)` — Obtiene detalle de un evento
- `useEventParticipants(id)` — Obtiene participantes de un evento con estado de certificado
- `useEventGenerateCertificates()` — Mutación para generar certificados de un evento
- `useUpdateEvent()` — Mutación para actualizar configuración del evento
