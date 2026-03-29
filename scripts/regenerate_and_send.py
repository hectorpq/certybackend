"""
Script para regenerar certificados y enviar con PDF adjuntado
"""
from certificados.models import Certificate
from users.models import User
from django.db.models import Q

print("\n" + "="*80)
print("REGENERAR CERTIFICADOS CON PDF REAL Y ENVIAR EMAIL")
print("="*80)

# Obtener admin
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    print("❌ No hay usuario admin")
    exit()

print(f"\n[1] Admin: {admin.email}")

# Obtener certificados viejos (con URL fake)
print("\n[2] Buscando certificados viejos (URL fake)...")
old_certs = Certificate.objects.filter(
    pdf_url__startswith='https://certificates.example.com'
)
print(f"   Encontrados: {old_certs.count()}")

for cert in old_certs[:5]:  # Procesar primeros 5
    print(f"\n   Procesando: {cert.student.first_name} - {cert.event.name}")
    
    # Resetear a pending
    cert.status = 'pending'
    cert.pdf_url = ''  # Limpiar URL vieja
    cert.save()
    print(f"   ✓ Status: pending")
    
    # Regenerar (crea PDF real)
    try:
        cert = cert.generate(generated_by=admin)
        print(f"   ✓ PDF generado: {cert.pdf_url}")
    except Exception as e:
        print(f"   ❌ Error en generación: {e}")
        continue
    
    # Enviar email con PDF adjuntado
    try:
        delivery_log = cert.deliver(
            method='email',
            recipient=cert.student.email,
            sent_by=admin
        )
        
        if delivery_log.status == 'success':
            print(f"   ✅ Email enviado CON PDF ADJUNTADO")
            print(f"      Destinatario: {cert.student.email}")
        else:
            print(f"   ⚠️  Email enviado pero con ERROR: {delivery_log.error_message}")
            
    except Exception as e:
        print(f"   ❌ Error al enviar: {e}")

print("\n" + "="*80)
print("✅ COMPLETADO")
print("="*80)
print("\nVerifica tu inbox - los PDFs deben estar ADJUNTADOS, no como link")
