# Diagrama de Contexto (C4 — Nivel 1)

## Propósito

Mostrar el sistema Certy en su contexto, interactuando con usuarios y sistemas externos.

## Elementos

| Elemento | Tipo | Descripción |
|----------|------|-------------|
| **Certy (Sistema)** | Sistema de software | Gestión y entrega de certificados |
| **Administrador** | Persona | Configura, audita, gestiona usuarios |
| **Coordinador** | Persona | Opera el día a día: eventos, participantes, certificados |
| **Participante** | Persona | Recibe y visualiza sus certificados |
| **Verificador** | Persona | Público general que verifica códigos de certificados |
| **SendGrid** | Sistema externo | API de envío de correos electrónicos |
| **Meta WhatsApp Cloud API** | Sistema externo | API de mensajería WhatsApp |
| **Google OAuth 2.0** | Sistema externo | Autenticación social |
| **PostgreSQL** | Base de datos | Almacenamiento persistente |
| **Redis** | Sistema externo | Broker de mensajería para Celery |

## Flujo Principal

```
Administrador/Coordinador ──HTTPS──> Certy (SPA + API)
Participante ──HTTPS──> Certy (SPA)
Verificador ──HTTPS──> Certy (API → verify endpoint)
Certy ──SMTP/API──> SendGrid
Certy ──HTTPS──> Meta WhatsApp Cloud API
Certy ──SQL──> PostgreSQL
Certy (Celery) ──TCP──> Redis
```

## Relaciones

- **Administrador → Certy:** Gestiona usuarios, visualiza auditoría, exporta datos
- **Coordinador → Certy:** Crea eventos, carga participantes, genera y envía certificados
- **Participante → Certy:** Visualiza certificados, descarga PDFs, actualiza perfil
- **Verificador → Certy:** Consulta `GET /api/certificates/verify/?code=XXXX`
- **Certy → SendGrid:** Envía correos con PDF adjunto
- **Certy → WhatsApp:** Envía mensajes con enlace de descarga
- **Certy → Google OAuth:** Valida tokens de identidad de Google
