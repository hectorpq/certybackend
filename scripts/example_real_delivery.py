"""
Ejemplo de uso de los servicios de entrega real
Ejecutar con: python manage.py shell < scripts/example_real_delivery.py
"""

from certificados.models import Certificate
from events.models import Event, Enrollment
from students.models import Student
from users.models import User
from services.email_service import EmailService
from services.pdf_service import PDFService
from services.whatsapp_service import get_whatsapp_service
from django.utils import timezone

print("\n" + "="*80)
print("DEMOSTRACIÓN - ENTREGAS REALES (Gmail, WhatsApp, PDF)")
print("="*80)

# ============================================================================
# 1. OBTENER DATOS DE PRUEBA
# ============================================================================
print("\n[1] Obteniendo datos de prueba...")

try:
    event = Event.objects.filter(is_active=True).first()
    if not event:
        print("❌ No hay eventos activos")
        exit()
    print(f"✓ Evento: {event.name}")
    
    # Obtener un estudiante inscrito y que asistió
    enrollment = Enrollment.objects.filter(
        event=event,
        attendance=True
    ).first()
    
    if not enrollment:
        print("❌ No hay estudiantes que hayan asistido")
        exit()
    
    student = enrollment.student
    print(f"✓ Estudiante: {student.first_name} {student.last_name}")
    print(f"  Email: {student.email}")
    print(f"  Teléfono: {student.phone or 'No registrado'}")
    
    admin_user = User.objects.filter(is_superuser=True).first()
    print(f"✓ Admin: {admin_user.email}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# ============================================================================
# 2. CREAR O RECUPERAR CERTIFICADO
# ============================================================================
print("\n[2] Creando/Recuperando certificado...")

try:
    certificate, created = Certificate.objects.get_or_create(
        student=student,
        event=event,
        defaults={'status': 'pending'}
    )
    
    if created:
        print(f"✓ Certificado creado (ID: {certificate.id})")
    else:
        print(f"✓ Certificado existe (ID: {certificate.id}, Status: {certificate.status})")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# ============================================================================
# 3. GENERAR CERTIFICADO (incluye PDF REAL)
# ============================================================================
print("\n[3] Generando certificado (crea PDF REAL)...")

try:
    if certificate.status == 'pending':
        certificate = certificate.generate(generated_by=admin_user)
        print(f"✓ Certificado generado")
        print(f"  Código: {certificate.verification_code}")
        print(f"  PDF URL: {certificate.pdf_url}")
        print(f"  Válido hasta: {certificate.expires_at.strftime('%d/%m/%Y')}")
    else:
        print(f"⚠️  Certificado ya está en estado: {certificate.status}")
    
except Exception as e:
    print(f"❌ Error en generación: {e}")
    exit()

# ============================================================================
# 4A. ENTREGAR POR EMAIL (REAL)
# ============================================================================
print("\n[4A] Entregando por EMAIL (REAL vía Gmail SMTP)...")

try:
    if not student.email:
        print("❌ El estudiante no tiene email registrado")
    else:
        # Método 1: Direct service call
        print(f"   Enviando a: {student.email}")
        result = EmailService.send_certificate(certificate, student.email)
        
        if result['success']:
            print(f"✅ Email enviado: {result['message']}")
            print(f"   Timestamp: {result.get('timestamp')}")
        else:
            print(f"❌ Error: {result['message']}")
            print("   (Verifica email config en .env: EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)")
except Exception as e:
    print(f"❌ Error de email: {e}")

# ============================================================================
# 4B. ENTREGAR POR EMAIL vía Certificate.deliver()
# ============================================================================
print("\n[4B] Entregando por EMAIL vía método deliver()...")

try:
    if certificate.status in ['generated', 'sent']:
        delivery_log = certificate.deliver(
            method='email',
            recipient=student.email,
            sent_by=admin_user
        )
        
        print(f"✓ DeliveryLog creado (ID: {delivery_log.id})")
        print(f"  Status: {delivery_log.status}")
        print(f"  Método: {delivery_log.get_delivery_method_display()}")
        print(f"  Destinatario: {delivery_log.recipient}")
        print(f"  Enviado por: {delivery_log.sent_by.email}")
        
        if delivery_log.status == 'error':
            print(f"  Error: {delivery_log.error_message}")
        else:
            print(f"✅ Certificado status cambió a: {certificate.status}")
    else:
        print(f"⚠️  El certificado debe estar en generated/sent, actual: {certificate.status}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# 5A. ENTREGAR POR WHATSAPP (REAL)
# ============================================================================
print("\n[5A] Entregando por WHATSAPP (REAL vía Twilio)...")

try:
    if not student.phone:
        print("❌ El estudiante no tiene teléfono registrado")
        print("   Formato requerido: +57 (país) + número")
    else:
        # Método 1: Direct service call
        whatsapp = get_whatsapp_service()
        print(f"   Enviando a: {student.phone}")
        
        result = whatsapp.send_certificate(certificate, student.phone)
        
        if result['success']:
            print(f"✅ WhatsApp enviado: {result['message']}")
            print(f"   Message SID: {result.get('sid')}")
        else:
            print(f"❌ Error: {result['message']}")
            print("   (Verifica Twilio config en .env: TWILIO_ACCOUNT_SID, AUTH_TOKEN, PHONE_NUMBER)")
            
except Exception as e:
    print(f"❌ Error de WhatsApp: {e}")

# ============================================================================
# 5B. ENTREGAR POR WHATSAPP vía Certificate.deliver()
# ============================================================================
print("\n[5B] Entregando por WHATSAPP vía método deliver()...")

try:
    if certificate.status in ['generated', 'sent']:
        if student.phone:
            delivery_log = certificate.deliver(
                method='whatsapp',
                recipient=student.phone,
                sent_by=admin_user
            )
            
            print(f"✓ DeliveryLog creado (ID: {delivery_log.id})")
            print(f"  Status: {delivery_log.status}")
            print(f"  Método: {delivery_log.get_delivery_method_display()}")
            print(f"  Número: {delivery_log.recipient}")
            
            if delivery_log.status == 'error':
                print(f"  Error: {delivery_log.error_message}")
        else:
            print("❌ Sin teléfono registrado")
    else:
        print(f"⚠️  El certificado debe estar en generated/sent, actual: {certificate.status}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# 6. HISTORIAL DE ENTREGAS
# ============================================================================
print("\n[6] Historial de entregas...")

try:
    delivery_history = certificate.get_delivery_history()
    
    if not delivery_history:
        print("❌ Sin intentos de entrega aún")
    else:
        print(f"✓ {delivery_history.count()} intentos registrados:")
        for i, delivery in enumerate(delivery_history, 1):
            icon = delivery.get_delivery_icon()
            status_icon = delivery.get_status_icon()
            print(f"  {i}. {status_icon} {icon} {delivery.get_delivery_method_display()}")
            print(f"     → {delivery.recipient}")
            print(f"     → {delivery.sent_at.strftime('%d/%m/%Y %H:%M:%S')}")
            if delivery.error_message:
                print(f"     → Error: {delivery.error_message}")
                
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# 7. ESTADO ACTUAL
# ============================================================================
print("\n[7] Estado actual del certificado...")

try:
    certificate = Certificate.objects.get(id=certificate.id)  # Reload
    
    print(f"✓ Evento: {certificate.event.name}")
    print(f"✓ Estudiante: {certificate.student.first_name} {certificate.student.last_name}")
    print(f"✓ Certificado ID: {certificate.id}")
    print(f"✓ Código: {certificate.verification_code}")
    print(f"✓ Status: {certificate.get_status_display()} (base de datos)")
    print(f"✓ Última entrega: {certificate.delivery_status}")
    print(f"✓ PDF: {certificate.pdf_url}")
    print(f"✓ Válido hasta: {certificate.expires_at.strftime('%d/%m/%Y')}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
print("✅ DEMOSTRACIÓN COMPLETADA")
print("="*80)
print("""
NOTAS:
1. Email real se envía SOLO si Gmail está configurado en .env
2. WhatsApp real se envía SOLO si Twilio está configurado en .env
3. PDF real se genera SIEMPRE que se llama generate()
4. DeliveryLog registra cada intento (success/error)
5. El status del certificado se actualiza automáticamente

Para ver los logs:
- /admin/certificados/certificate/ → Ver historial en cada certificado
- /admin/deliveries/deliverylog/ → Ver todos los intentos de entrega
""")
