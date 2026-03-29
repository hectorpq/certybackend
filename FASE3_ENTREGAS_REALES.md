# Fase 3 - Entregas Reales: Gmail, WhatsApp y PDF

## ✅ Implementado

El sistema ahora envía certificados REALES via:
- 📧 **Email (Gmail SMTP)** - Correos auténticos con PDF
- 💬 **WhatsApp (Twilio API)** - Mensajes automáticos
- 🔗 **Link directo** - Acceso sin verificación

## 🔧 Configuración Requerida

### 1. Google Gmail SMTP

**Paso 1: Obtener credenciales**
1. Ve a: https://myaccount.google.com/security
2. Activa "2-Step Verification"
3. Busca "App passwords"
4. Selecciona "Mail" → "Windows Computer"
5. Copia la contraseña generada

**Paso 2: Configurar en .env**
```env
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=contraseña-de-app
DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

**Validar:**
```bash
python manage.py shell
from django.core.mail import send_mail
send_mail(
    'Test',
    'Message',
    'tu-email@gmail.com',
    ['destino@gmail.com'],
    fail_silently=False,
)
```

### 2. Twilio WhatsApp API

**Paso 1: Crear cuenta**
1. Ve a: https://www.twilio.com
2. Regístrate
3. Ve a Console → Account SID (copia)
4. Ve a Auth Token (copia)

**Paso 2: Configurar número WhatsApp**
1. En Twilio: Messaging → Services → Create Service
2. Send a Message with Twilio → WhatsApp
3. Sigue el setup para obtener número

**Paso 3: Configurar en .env**
```env
TWILIO_ACCOUNT_SID=tu-account-sid
TWILIO_AUTH_TOKEN=tu-auth-token
TWILIO_PHONE_NUMBER=+15551234567
```

**Validar:**
```bash
python manage.py shell
from services.whatsapp_service import get_whatsapp_service
ws = get_whatsapp_service()
result = ws.send_certificate(certificado, '+57300000000')
print(result)
```

## 📁 Estructura de Archivos

```
services/
├─ __init__.py              # Exports
├─ email_service.py         # EmailService - SMTP
├─ pdf_service.py           # PDFService - reportlab
└─ whatsapp_service.py      # WhatsAppService - Twilio
```

## 🎯 Cómo Funciona

### Antes (Fase 2)
```python
certificate.deliver()
→ Simula envío
→ Registra en BD
→ Sin email real
```

### Ahora (Fase 3)
```python
certificate.deliver(method='email', recipient='...')
→ Genera PDF REAL con reportlab
→ Envía email REAL vía Gmail SMTP
→ Crea DeliveryLog con status real (success/error)
→ Actualiza Certificate.status

certificate.deliver(method='whatsapp', recipient='+57...')
→ Envía vía Twilio WhatsApp API
→ Logs de error autómatico

certificate.deliver(method='link', recipient=None)
→ Solo marca como delivered
→ Sin envío, solo disponible por link
```

## 🖱️ Flujo en Admin

### Generar Certificados
1. `/admin/certificados/certificate/`
2. Selecciona pending
3. Acción: **✅ Generate Certificates**
4. ✅ Genera PDF real
5. PDF guardado en `/certificates/pdfs/`

### Entregar por Email
1. Selecciona generated/sent
2. Acción: **📧 Deliver via Email (REAL EMAIL)**
3. ✅ Envía email REAL vía Gmail
4. Crea DeliveryLog con timestamp
5. Status actualizado a "sent"

### Entregar por WhatsApp
1. Selecciona generated/sent
2. Acción: **💬 Deliver via WhatsApp (REAL WHATSAPP)**
3. ✅ Envía mensaje de WhatsApp REAL
4. Valida número telefónico
5. Status actualizado a "sent"

### Entregar por Link
1. Selecciona generated/sent
2. Acción: **🔗 Mark as Delivered (Direct Link)**
3. ✅ Marca como entregado por link directo
4. Sin envío real
5. Status: "sent"

## 📊 Estados del Certificado

```
Pending → Generate → Generated
                        ↓
                    Deliver (Email/WhatsApp/Link)
                        ↓
                      Sent ← Retry
                        ↓
                      Failed
```

## 🐛 Manejo de Errores

Si falla el envío:
- ❌ DeliveryLog status: 'error'
- 📝 error_message: razón del error
- 🔄 Puedes reintentar: Reset to Pending → Generate → Deliver

**Errores comunes:**
1. "Email not configured" → Ver .env EMAIL_*
2. "Google 2FA" → Usar App Password, no contraseña normal
3. "Twilio not configured" → Ver .env TWILIO_*
4. "Invalid phone" → Asegurate formato: +57300000000
5. "Student phone is None" → Añade teléfono al Student

## 🔍 Validación

```bash
# Check email config
python manage.py shell
>>> from django.conf import settings
>>> settings.EMAIL_HOST_USER
>>> settings.EMAIL_HOST_PASSWORD

# Check Twilio config
>>> from services.whatsapp_service import get_whatsapp_service
>>> ws = get_whatsapp_service()
>>> ws.client is not None
True

# Check PDF path
>>> from django.conf import settings
>>> settings.CERTIFICATES_PDF_PATH.exists()
True
```

## 📦 Dependencias Instaladas

```
reportlab==4.0.7           # PDF generation
twilio==8.10.0             # WhatsApp API
django-environ==0.10.0     # .env support
```

## 🚀 Próximos Pasos (Future)

- [ ] Webhook para notificaciones
- [ ] Cron job para entregas automáticas
- [ ] Dashboard de entregas
- [ ] Reportes de éxito/fallo
- [ ] QR en PDF
- [ ] Firma digital
- [ ] API REST para entregas

## 📝 Notas Importantes

1. **PDF Real:** Se genera cuando `generate()`
   - Guardado en `/certificates/pdfs/`
   - Nombre: `{student_id}_{event_id}_{code}.pdf`
   - Validez: 365 días

2. **Email Real:** Se envía cuando `deliver(method='email')`
   - Via SMTP Gmail
   - Requiere credenciales configuradas
   - Logs en admin

3. **WhatsApp Real:** Se envía cuando `deliver(method='whatsapp')`
   - Via API Twilio
   - Requiere número telefónico
   - Sandbox mode initially (solo numbers registered)

4. **Database Tracking:**
   - DeliveryLog registro automático
   - sent_at timestamp exacto
   - Status: pending/success/error
   - error_message guardado
   - sent_by: usuario que envió

---

**Estado:** ✅ Implementado
**Fecha:** 29/03/2026
**Ambiente:** Listo para testing
