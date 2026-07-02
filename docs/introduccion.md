# Introducción

## Propósito del Sistema

Certy es una plataforma web para la **gestión del ciclo de vida completo de certificados académicos**: desde la planificación del evento y el diseño visual de la plantilla hasta la generación del PDF con elementos de seguridad (código QR de verificación, firma digital) y la **distribución omnicanal** (email, WhatsApp, enlace público).

## Problema que Resuelve

Las instituciones educativas y organizadores de eventos enfrentan estos desafíos:

- **Proceso manual:** Emitir certificados uno por uno consumiendo horas de trabajo administrativo
- **Falta de trazabilidad:** No hay registro de quién generó, cuándo y cómo se entregó cada certificado
- **Verificación limitada:** Los certificados en papel son difíciles de autenticar
- **Distribución ineficiente:** Enviar certificados por correo electrónico individualmente
- **Personalización compleja:** Dificultad para adaptar el diseño visual a cada evento

Certy resuelve estos problemas automatizando cada etapa.

## Usuarios del Sistema

- **Administradores** — Configuración general, auditoría, gestión de usuarios del sistema
- **Coordinadores** — Operación diaria: creación de eventos, carga de participantes, generación y envío de certificados
- **Participantes** — Visualización y descarga de sus propios certificados
- **Instructores** — Asociados a eventos como firmantes de certificados
- **Verificadores** — Público general que verifica la autenticidad de un certificado mediante su código único

## Alcance

### Incluye

- Creación y gestión de eventos académicos con estados (borrador, activo, finalizado, cancelado)
- Diseño visual interactivo de plantillas de certificados
- Carga masiva de participantes desde Excel/CSV
- Generación automatizada de PDFs con código QR y firma digital
- Distribución por email (SendGrid), WhatsApp (Meta Cloud API) y enlace público
- Verificación pública de certificados mediante código único
- Roles y permisos (admin, coordinador, participante)
- Historial de entregas y reintentos
- Registro de auditoría de acciones críticas

### Excluye

- Facturación o pagos
- Gestión de aulas o recursos físicos
- Transmisión en vivo de eventos
- Evaluaciones o calificaciones automatizadas
- Integración con LMS de terceros

## Documentos Relacionados

- Project Charter (documento de constitución del proyecto)
- Plan de auditoría SDLC
- Manuales de usuario por rol
