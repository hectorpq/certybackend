# Manual del Coordinador

## Gestión de Eventos

1. Ir a "Eventos" en el menú lateral
2. Hacer clic en "Crear Evento"
3. Completar formulario:
    - Nombre del evento (requerido)
    - Fecha de inicio y fin
    - Duración en horas
    - Ubicación
    - Categoría (opcional)
    - Instructor (opcional)
    - Estado inicial: borrador
4. Guardar

### Estados de Evento

| Estado | Descripción |
|--------|-------------|
| **Borrador** | En preparación, aún no visible |
| **Activo** | Evento en curso, visible para participantes |
| **Finalizado** | Evento terminado, listo para generar certificados |
| **Cancelado** | Evento cancelado |

## Inscripción de Participantes

**Individual:**
1. Abrir detalle del evento
2. Buscar participante por nombre o email
3. Seleccionar y confirmar inscripción

**Masiva (desde Excel):**
1. Ir a "Generación Masiva" → pestaña "Por Excel"
2. Seleccionar evento
3. Subir archivo Excel con columnas: `full_name`, `email`, `document_id`
4. Revisar vista previa de datos
5. Confirmar procesamiento

## Diseño de Certificado

1. Ir a "Plantillas" en el menú lateral
2. Crear nueva plantilla o editar existente
3. Subir imagen de fondo (PNG/JPG)
4. Hacer clic en la imagen para definir posición X/Y del nombre
5. Ajustar tamaño de fuente (slider 12pt-72pt)
6. Seleccionar color del texto
7. Subir firma digital del instructor (opcional)
8. Guardar plantilla

## Generación de Certificados

**Desde evento:**
1. Abrir detalle del evento
2. Marcar asistencia de participantes
3. Hacer clic en "Generar Certificados"
4. Seleccionar: todos los asistentes o participantes específicos
5. Confirmar

**Masiva (desde Excel):**
1. Ir a "Generación Masiva"
2. Seleccionar evento
3. Subir Excel con participantes
4. Configurar plantilla visual
5. Generar y enviar

## Envío de Certificados

1. Desde el detalle del evento, hacer clic en "Enviar Certificados"
2. Seleccionar método: Email, WhatsApp o Link
3. Confirmar envío
4. Ver resultados (éxitos y fallos)

## Registro de Asistencia

1. Abrir detalle del evento
2. En la lista de participantes, activar/desactivar el toggle de asistencia
3. La asistencia se guarda automáticamente
