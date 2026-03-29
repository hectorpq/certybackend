"""
Script de demostración - FASE 2: Núcleo del Negocio
====================================================

Este script demuestra el flujo completo:
  Evento → Estudiante → Certificado → Entrega

Uso: python manage.py shell < scripts/demo_fase2.py
"""

from django.contrib.auth import get_user_model
from events.models import Event, Enrollment
from certificados.models import Template, Certificate
from deliveries.models import DeliveryLog

User = get_user_model()

print("\n" + "="*80)
print("DEMOSTRACIÓN - FASE 2: NÚCLEO DEL NEGOCIO")
print("="*80)

# 1. Obtener datos de prueba existentes
print("\n[1] Obteniendo datos de prueba...")

try:
    event = Event.objects.filter(status='active').first()
    if not event:
        print("❌ No hay eventos activos")
        exit()
    
    print(f"✓ Evento: {event.name}")
    
    # Obtener estudiante con inscripción
    enrollment = event.enrollments.filter(attendance=True).first()
    if not enrollment:
        print("❌ No hay estudiantes inscritos con asistencia")
        exit()
    
    student = enrollment.student
    print(f"✓ Estudiante: {student.full_name}")
    
    # Obtener plantilla
    template = Template.objects.filter(is_active=True).first()
    if not template:
        print("❌ No hay plantillas activas")
        exit()
    
    print(f"✓ Plantilla: {template.name}")
    
    admin_user = User.objects.filter(role='admin').first()
    print(f"✓ Admin: {admin_user.full_name}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# 2. Crear o encontrar certificado
print("\n[2] Creando certificado...")

try:
    certificate, created = Certificate.objects.get_or_create(
        student=student,
        event=event,
        defaults={
            'template': template,
            'status': 'pending'
        }
    )
    
    if created:
        print(f"✓ Certificado creado para {student.first_name}")
    else:
        print(f"✓ Certificado ya existe para {student.first_name}")
        if certificate.status != 'pending':
            print(f"   Status actual: {certificate.status}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# 3. Generar certificado
print("\n[3] Generando certificado...")

try:
    if certificate.status == 'pending':
        certificate.generate(
            template=template,
            generated_by=admin_user
        )
        print(f"✅ Certificado generado")
        print(f"   Código: {certificate.verification_code}")
        print(f"   Status: {certificate.status}")
    else:
        print(f"⚠️  Certificado ya está en estado: {certificate.status}")
except Exception as e:
    print(f"❌ Error al generar: {e}")

# 4. Simular entrega
print("\n[4] Simulando entrega...")

try:
    if certificate.status in ['generated', 'sent']:
        delivery = certificate.deliver(
            method='email',
            recipient=student.email,
            sent_by=admin_user
        )
        print(f"✅ Entrega simulada")
        print(f"   Método: {delivery.get_delivery_method_display()}")
        print(f"   Destinatario: {delivery.recipient}")
        print(f"   Status: {delivery.get_status_display()}")
    else:
        print(f"⚠️  Certificado debe estar generado primero")
except Exception as e:
    print(f"❌ Error al entregar: {e}")

# 5. Ver historial de entregas
print("\n[5] Historial de entregas...")

deliveries = certificate.get_delivery_history()
print(f"Total entregas: {deliveries.count()}")

for delivery in deliveries:
    icon = delivery.get_status_icon()
    method_icon = delivery.get_delivery_icon()
    print(f"  {icon} {method_icon} {delivery.get_delivery_method_display()} → {delivery.recipient}")

# 6. Resumen final
print("\n" + "="*80)
print("RESUMEN - FLUJO COMPLETADO")
print("="*80)

print(f"""
✓ Evento:      {event.name}
✓ Estudiante:  {student.full_name}
✓ Certificado: {certificate.status.upper()}
  └─ Código: {certificate.verification_code}
✓ Entregas:    {deliveries.count()} intentos
  └─ Última: {certificate.last_delivery_attempt.status if certificate.last_delivery_attempt else 'N/A'}

PRÓXIMOS PASOS EN ADMIN:
1. Ir a http://localhost:8000/admin/certificados/certificate/
2. Ver acciones disponibles:
   ✅ Generate Certificates
   📧 Deliver Certificates
   ❌ Mark as Failed
   ↩️  Reset to Pending
3. Hacer click en certificado para ver detalles
4. Ir a Delivery Logs para ver historial completo
""")

print("="*80)
print("✅ DEMOSTRACIÓN COMPLETADA")
print("="*80)
