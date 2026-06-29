# Procesos de Importación y Generación Masiva — `procesos/services.py`

## `ExcelProcessingService`

Servicio principal para procesar archivos Excel/CSV con datos de participantes y generar certificados en lote.

### Pipeline de Procesamiento

```
Archivo Excel/CSV
    → _read_excel_file()         # Lectura + detección de formato
        → _validate_columns()     # Verifica columnas requeridas
            → _process_rows()     # Itera fila por fila
                → _process_row()  # Por cada fila:
                    1. _validate_email()
                    2. _get_or_create_participant()
                    3. _get_event()
                    4. _get_or_create_enrollment()
                    5. _create_certificate()
                        → _generate_verification_code()
```

**Columnas requeridas:** `full_name`, `email`, `document_id`

**Columnas opcionales:** `event_name`, `phone`, `institution`, `certificate_template`

### Métodos Clave

- `read_and_validate_structure(excel_file)` — Lee y valida la estructura del archivo, retorna datos para previsualización
- `process_records(records)` — Procesa registros validados/editados desde el frontend
- `validate_file(excel_file)` — Validación rápida del archivo (sin procesar datos)

## `BulkCertificateGeneratorService`

Capa de alto nivel que orquesta `ExcelProcessingService` para generación masiva.

### `generate_from_excel(excel_file, background_image, event_id, ...)`

Método estático que recibe:
- Archivo Excel con datos de participantes
- Imagen de fondo para el certificado
- Configuración visual (posición X/Y, tamaño de fuente, color)
- Datos de firma digital (imagen, nombre, especialidad del instructor)

## `ExcelProcessingResult`

Contenedor de resultados:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total_rows` | `int` | Total de filas procesadas |
| `successful` | `int` | Registros exitosos |
| `failed` | `int` | Registros fallidos |
| `errors` | `list` | Detalle de errores (row, field, message, data) |
| `created_certificates` | `list[int]` | IDs de certificados creados |
| `data_preview` | `list[dict]` | Datos extraídos para previsualización |
| `processing_timestamp` | `str` | Marca de tiempo del procesamiento |
| `summary` | `str` | Resumen textual |

## Excepciones

- `ExcelImportError(Exception)` — Error personalizado para fallos de importación
