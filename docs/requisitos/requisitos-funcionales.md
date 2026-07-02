# Requisitos Funcionales

## Módulo de Autenticación

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RF-01 | El sistema debe permitir registro de usuarios con email, nombre y contraseña | Alta |
| RF-02 | El sistema debe permitir inicio de sesión con email y contraseña | Alta |
| RF-03 | El sistema debe permitir inicio de sesión con Google OAuth2 | Alta |
| RF-04 | El sistema debe emitir tokens JWT (access 8h, refresh 7d) | Alta |
| RF-05 | El sistema debe renovar tokens automáticamente (refresh rotation) | Alta |
| RF-06 | El sistema debe cerrar sesión y limpiar tokens | Alta |

## Módulo de Eventos

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RF-10 | El sistema debe permitir CRUD de eventos (nombre, fecha, ubicación, etc.) | Alta |
| RF-11 | El sistema debe soportar estados: draft, active, finished, cancelled | Alta |
| RF-12 | El sistema debe permitir asociar un instructor al evento | Alta |
| RF-13 | El sistema debe permitir inscribir participantes individualmente | Alta |
| RF-14 | El sistema debe permitir inscribir participantes masivamente desde Excel/CSV | Alta |
| RF-15 | El sistema debe permitir registrar asistencia de participantes | Alta |
| RF-16 | El sistema debe permitir generar certificados para todos los asistentes | Alta |
| RF-17 | El sistema debe permitir enviar certificados por lote (email/whatsapp/link) | Alta |
| RF-18 | El sistema debe permitir enviar invitaciones por email | Media |
| RF-19 | El sistema debe permitir finalizar un evento con auto-generación de certificados | Media |

## Módulo de Certificados

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RF-20 | El sistema debe generar PDFs personalizados con nombre del participante | Alta |
| RF-21 | El sistema debe incluir código QR de verificación único en cada PDF | Alta |
| RF-22 | El sistema debe incluir firma digital del instructor | Alta |
| RF-23 | El sistema debe permitir configurar la posición del nombre sobre la plantilla | Alta |
| RF-24 | El sistema debe permitir verificar la autenticidad mediante código único | Alta |
| RF-25 | El sistema debe registrar el historial de entregas de cada certificado | Alta |
| RF-26 | El sistema debe permitir reintentar entregas fallidas | Media |

## Módulo de Participantes

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RF-30 | El sistema debe permitir CRUD de participantes con documento, nombre, email | Alta |
| RF-31 | El sistema debe permitir importar participantes desde Excel/CSV | Alta |
| RF-32 | El sistema debe detectar duplicados por email o documento | Media |

## Módulo de Plantillas

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RF-35 | El sistema debe permitir CRUD de plantillas con imagen de fondo | Alta |
| RF-36 | El sistema debe permitir posicionar interactivamente el nombre sobre la imagen | Alta |
| RF-37 | El sistema debe permitir configurar tamaño y color de fuente | Alta |
| RF-38 | El sistema debe permitir subir firma digital para instructores | Alta |

## Módulo de Auditoría

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RF-40 | El sistema debe registrar generación de certificados en AuditLog | Alta |
| RF-41 | El sistema debe registrar entregas de certificados en AuditLog | Alta |
| RF-42 | El sistema debe registrar inicios de sesión (exitosos y fallidos) | Media |
| RF-43 | El sistema debe permitir visualizar el log de auditoría (solo admin) | Alta |
