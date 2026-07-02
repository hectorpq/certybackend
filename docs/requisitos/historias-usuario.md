# Historias de Usuario

## Administrador

| ID | Historia | Criterios de Aceptación |
|----|----------|------------------------|
| HU-01 | Como administrador, quiero gestionar usuarios (crear, editar, desactivar) para controlar quién accede al sistema | 1. CRUD de usuarios funcionando. 2. Solo admin puede acceder. 3. Los cambios son inmediatos |
| HU-02 | Como administrador, quiero ver el log de auditoría para rastrear acciones críticas | 1. Lista paginada de eventos. 2. Filtros por acción y usuario. 3. Timestamp e IP visibles |
| HU-03 | Como administrador, quiero exportar certificados a CSV/Excel para análisis externos | 1. Exportación con filtros. 2. Formato seleccionable (CSV/Excel) |

## Coordinador

| ID | Historia | Criterios de Aceptación |
|----|----------|------------------------|
| HU-10 | Como coordinador, quiero crear un evento con fecha, ubicación y categoría para organizar la entrega de certificados | 1. Formulario con todos los campos. 2. Evento creado en estado draft. 3. Puedo editarlo después |
| HU-11 | Como coordinador, quiero cargar un archivo Excel con participantes para inscribirlos masivamente a un evento | 1. Subir archivo .xlsx/.xls. 2. Validar estructura (columnas requeridas). 3. Vista previa de datos. 4. Procesar con retroalimentación de errores |
| HU-12 | Como coordinador, quiero diseñar la plantilla del certificado subiendo una imagen y posicionando el nombre para personalizar la entrega | 1. Subir imagen PNG/JPG. 2. Click en la imagen para definir X/Y. 3. Slider de tamaño de fuente. 4. Selector de color |
| HU-13 | Como coordinador, quiero generar los PDFs de certificados para un evento completo con un solo clic | 1. Seleccionar evento. 2. Opción: todos los asistentes o selección. 3. Procesamiento asíncrono con feedback |
| HU-14 | Como coordinador, quiero enviar los certificados generados por email a todos los participantes del evento | 1. Seleccionar método (email/whatsapp/link). 2. Envío en lote. 3. Ver resultados (éxitos/fallos) |
| HU-15 | Como coordinador, quiero registrar la asistencia de los participantes al evento | 1. Lista de inscritos. 2. Toggle de asistencia. 3. Persistencia inmediata |

## Participante

| ID | Historia | Criterios de Aceptación |
|----|----------|------------------------|
| HU-20 | Como participante, quiero ver mis certificados emitidos para descargarlos | 1. Lista filtrada por mi email. 2. Enlace de descarga PDF. 3. Código de verificación visible |
| HU-21 | Como participante, quiero verificar que un certificado es auténtico usando su código único | 1. Ingresar código. 2. Ver datos del certificado. 3. Sin autenticación requerida |

## Verificador (Público)

| ID | Historia | Criterios de Aceptación |
|----|----------|------------------------|
| HU-30 | Como verificador, quiero consultar la validez de un certificado con su código para confirmar su autenticidad | 1. Formulario público de verificación. 2. Respuesta con datos del certificado. 3. Sin login requerido |
