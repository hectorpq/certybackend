# CHECKLIST - Puesta en Marcha de Entregas Reales

## ✅ Lo que YA está hecho

- [x] Servicios de email, PDF, WhatsApp creados
- [x] Métodos Certificate.generate() y deliver() actualizados
- [x] Acciones en admin creadas
- [x] Dependencias instaladas (reportlab, twilio)
- [x] Configuración en settings.py lista
- [x] .env con variables de ejemplo
- [x] Django check: OK
- [x] Validación: No errors

## 📋 TODO: Configurar Servicios Reales

### 1. Gmail SMTP (Para envío de emails)

[ ] 1.1 Ir a: https://myaccount.google.com/security
[ ] 1.2 Activar "2-Step Verification" (si no lo está)
[ ] 1.3 Ir a: https://myaccount.google.com/apppasswords
[ ] 1.4 Seleccionar:
      - App: Mail
      - Device: Windows Computer (o tu SO)
[ ] 1.5 Copiar contraseña generada (16 caracteres)
[ ] 1.6 Actualizar .env:
      ```
      EMAIL_HOST_USER=tu-email@gmail.com
      EMAIL_HOST_PASSWORD=contraseña-de-16-caracteres
      DEFAULT_FROM_EMAIL=tu-email@gmail.com
      ```
[ ] 1.7 Guardar y reiniciar Django
[ ] 1.8 Testear:
      ```bash
      python manage.py shell
      from django.core.mail import send_mail
      send_mail('Test', 'Mensaje', 'tu-email@gmail.com', ['destino@gmail.com'])
      ```

### 2. Twilio WhatsApp (Para envío de WhatsApp)

[ ] 2.1 Ir a: https://www.twilio.com/console
[ ] 2.2 Crear cuenta (o loguear si ya existe)
[ ] 2.3 En Console, copiar:
      - Account SID
      - Auth Token
[ ] 2.4 Ir a: Messaging → Services
[ ] 2.5 Click: Create Service
[ ] 2.6 Seleccionar: Send a Message with Twilio
[ ] 2.7 Seleccionar: WhatsApp
[ ] 2.8 Sigue el setup para obtener número de teléfono
      (Ejemplo: +15551234567)
[ ] 2.9 Actualize .env:
      ```
      TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      TWILIO_PHONE_NUMBER=+15551234567
      ```
[ ] 2.10 Guardar y reiniciar Django
[ ] 2.11 Testear:
       ```bash
       python manage.py shell
       from services.whatsapp_service import get_whatsapp_service
       ws = get_whatsapp_service()
       result = ws.send_certificate(cert, '+57300000000')
       print(result)
       ```

### 3. Directorio de PDFs

[ ] 3.1 Django crea automáticamente /certificates/pdfs/
[ ] 3.2 Verificar que existe:
      ```bash
      ls -la certificates/pdfs/
      ```

## 🧪 Testear Flujos

### Flujo: Generar PDF real
[ ] 4.1 Ir a: /admin/certificados/certificate/
[ ] 4.2 Seleccionar certificado pending
[ ] 4.3 Acción: ✅ Generate Certificates
[ ] 4.4 Verificar:
      - Status: pending → generated
      - PDF generado en /certificates/pdfs/
      - Código verificación asignado
[ ] 4.5 Buscar archivo:
      ```bash
      ls -la certificates/pdfs/*.pdf
      ```

### Flujo: Entregar por EMAIL real
[ ] 5.1 Certificado debe estar en "generated"
[ ] 5.2 Seleccionar en admin
[ ] 5.3 Acción: 📧 Deliver via Email (REAL EMAIL)
[ ] 5.4 Verificar:
      - Mensaje: "X certificados entregados via EMAIL"
      - Email recibido en buzón
      - DeliveryLog creado: /admin/deliveries/deliverylog/
      - Status: "sent"
[ ] 5.5 Si no llega email:
      - Revisar SPAM
      - Verificar .env EMAIL_HOST_USER
      - Revisar Gmail "Allow less secure apps" (Legacy)

### Flujo: Entregar por WHATSAPP real
[ ] 6.1 Certificado debe estar en "generated"
[ ] 6.2 Estudiante debe tener teléfono: +57300000000
[ ] 6.3 Seleccionar en admin
[ ] 6.4 Acción: 💬 Deliver via WhatsApp (REAL WHATSAPP)
[ ] 6.5 Verificar:
      - Mensaje: "X certificados entregados via WhatsApp"
      - WhatsApp recibido en teléfono
      - DeliveryLog: status "success"
[ ] 6.6 Si falla:
      - Revisar número teléfono (debe ser +57...)
      - Revisir TWILIO_ACCOUNT_SID y AUTH_TOKEN
      - Número debe registrado en Twilio (sandbox mode)

### Flujo: Completo (End-to-End)
[ ] 7.1 Ir a /admin/certificados/certificate/
[ ] 7.2 Seleccionar pending
[ ] 7.3 Acción: ✅ Generate Certificates
[ ] 7.4 Seleccionar generados
[ ] 7.5 Acción: 📧 Deliver via Email
[ ] 7.6 Verificar email recibido
[ ] 7.7 En /admin/ → Delivery Logs
[ ] 7.8 Ver historial de entregas
[ ] 7.9 Status del certificado debe ser "sent"

## 🔍 Validación

### Health Check
[ ] 8.1 python manage.py check → "No issues"
[ ] 8.2 ls services/ → email_service.py, pdf_service.py, whatsapp_service.py
[ ] 8.3 ls certificates/pdfs/ → archivos PDF presentes
[ ] 8.4 cat .env → EMAIL_HOST_USER, TWILIO_ACCOUNT_SID populated

### Database
[ ] 8.5 /admin/certificados/certificate/ → Ver certificados
[ ] 8.6 /admin/deliveries/deliverylog/ → Ver entregas
[ ] 8.7 Status: "sent" en varios certificados

## 📧 Troubleshooting

### Email no llega
```
Checklist:
1. ¿Gmail App password en .env? (16 caracteres)
2. ¿EMAIL_HOST_USER correcto?
3. ¿DEFAULT_FROM_EMAIL igual?
4. ¿Django reiniciado después de cambiar .env?
5. ¿Email en SPAM?
6. ¿Con 2FA habilitado en Gmail?
```

### WhatsApp no llega
```
Checklist:
1. ¿TWILIO_ACCOUNT_SID correcto?
2. ¿TWILIO_AUTH_TOKEN correcto?
3. ¿TWILIO_PHONE_NUMBER correcto? (+XXXX...)
4. ¿Teléfono del estudiante registrado? (+57...)
5. ¿Twilio en Sandbox? (solo números registrados)
6. ¿Django reiniciado después de cambiar .env?
```

### PDF no se genera
```
Checklist:
1. ¿reportlab instalado? pip list | grep reportlab
2. ¿/certificates/pdfs/ existe? ls -la certificates/
3. ¿Permisos de escritura? chmod 755 certificates/pdfs/
4. ¿Error en Django logs?
```

## 📊 Overview de Comandos Útiles

```bash
# Instalar dependencias
pip install reportlab twilio django-environ

# Check Django
python manage.py check

# Ver estado
python manage.py shell
from django.conf import settings
settings.EMAIL_HOST_USER  # Debe tener valor
settings.TWILIO_ACCOUNT_SID  # Debe tener valor

# Testear email
from django.core.mail import send_mail
send_mail('Test', 'Body', 'from@gmail.com', ['to@gmail.com'])

# Testear WhatsApp
from services.whatsapp_service import get_whatsapp_service
ws = get_whatsapp_service()
print(ws.client is not None)  # Debe ser True

# Ver PDF generados
ls -la certificates/pdfs/

# Ver logs de Django
tail -f logs/django.log  # Si existe
```

## 🚀 Siguiente

Una vez todo funcione:

1. Documentar en wiki o README
2. Entrenar al equipo
3. Empezar a usar en producción
4. Monitorear entregas en /admin/deliveries/
5. Considerar Fase 4 (webhooks, cron jobs, etc)

---

**Estado:** Checklist para configuración post-implementación
**Fecha:** 29/03/2026
**Duración estimada:** 2-3 horas (dependiendo de familiaridad con APIs)

