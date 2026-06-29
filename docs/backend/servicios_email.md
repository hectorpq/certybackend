# Servicio: Envío de Correos

El envío de correos electrónicos es un componente crucial para la entrega de certificados, notificaciones e invitaciones. El sistema utiliza **SendGrid** como proveedor de servicios de email transaccional.

## Configuración

La integración con SendGrid se configura a través de variables de entorno en el archivo `.env` del backend.

```env
# certybackend/.env

SENDGRID_API_KEY=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@certypro.app
```

## Funcionamiento

El método `certificate.deliver(method='email')` invoca al `EmailService`. Este servicio construye un correo electrónico con un mensaje predefinido, adjunta el PDF del certificado y lo envía al destinatario.

Cada intento de envío, ya sea exitoso o fallido, queda registrado en el modelo `DeliveryLog`.