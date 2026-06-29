# Flujo de Carga Masiva (Bulk)

La funcionalidad de carga masiva permite a los coordinadores y administradores generar cientos de certificados a partir de un archivo Excel, simplificando drásticamente el proceso.

## Proceso en el Frontend

El flujo se divide en dos pasos principales para garantizar la calidad de los datos antes del procesamiento final.

### Paso 1: Previsualización y Edición

1.  **Carga del Archivo**: El usuario selecciona un archivo Excel (`.xlsx`) y una imagen de plantilla (`.png`/`.jpg`).
2.  **Petición a `/api/certificates/preview/`**: El frontend envía el archivo Excel al backend.
3.  **Respuesta del Backend**: El backend valida la estructura del archivo y devuelve los datos extraídos en formato JSON.
4.  **Renderizado en Tabla**: El frontend muestra los datos en una tabla editable. Esto permite al usuario corregir nombres, emails o cualquier otro campo directamente en la interfaz antes de continuar.

### Paso 2: Procesamiento Final

1.  **Confirmación del Usuario**: Una vez que el usuario ha revisado y (opcionalmente) editado los datos, hace clic en "Generar Certificados".
2.  **Petición a `/api/certificates/process/` (o `generate-bulk`)**: El frontend envía el array de datos (ya limpios y editados) junto con el ID del evento y la imagen de la plantilla al backend.
3.  **Procesamiento en Backend**: El backend itera sobre cada registro, crea los participantes, las inscripciones y genera los certificados.
4.  **Resumen de Resultados**: El backend devuelve un resumen detallado del proceso: cuántos certificados se crearon con éxito, cuántos fallaron y una lista de errores específicos por fila.
5.  **Feedback al Usuario**: El frontend muestra este resumen al usuario, permitiéndole identificar y corregir fácilmente cualquier problema para un futuro intento.