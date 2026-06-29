# Servicio: Envío de WhatsApp

El sistema se integra con la **API de WhatsApp Cloud de Meta (Facebook)** para permitir el envío de notificaciones y enlaces de certificados.

!!! warning "Proveedor de Servicio"
    La implementación actual utiliza la API de Meta, no Twilio. La documentación anterior que mencionaba Twilio está desactualizada.

## Configuración

La integración requiere credenciales de una aplicación de Meta para desarrolladores, que se configuran en el archivo `.env` del backend.

```env
# certybackend/.env

META_WHATSAPP_TOKEN=your-meta-api-token
META_WHATSAPP_PHONE_ID=your-whatsapp-phone-number-id
```

## Funcionamiento

El método `certificate.deliver(method='whatsapp')` invoca al `WhatsAppService`. Este servicio se comunica con la API de Meta para enviar un mensaje de plantilla al número de teléfono del participante.

- El mensaje contiene un enlace para ver y descargar el certificado.
- Es requisito que el `Participant` tenga un número de teléfono válido registrado.
- Cada intento de envío queda registrado en el modelo `DeliveryLog`.