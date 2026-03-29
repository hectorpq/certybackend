"""
Regenerar TODOS los certificados sin PDF válido
"""
from certificados.models import Certificate
from users.models import User
from django.db.models import Q

admin = User.objects.filter(is_superuser=True).first()

print("\n" + "="*80)
print("REGENERANDO TODOS LOS CERTIFICADOS")
print("="*80 + "\n")

# Buscar certificados sin PDF o con URL vieja
bad_certs = Certificate.objects.filter(
    Q(pdf_url='') | 
    Q(pdf_url__startswith='https://example.com') |
    Q(pdf_url__startswith='https://certificates.example.com')
)

print(f"Certificados a regenerar: {bad_certs.count()}\n")

for cert in bad_certs:
    print(f"Procesando: {cert.student.first_name} - {cert.event.name}")
    
    # Limpiar y resetear
    cert.status = 'pending'
    cert.pdf_url = ''
    cert.save()
    
    try:
        # Generar PDF real
        cert = cert.generate(generated_by=admin)
        print(f"  ✓ PDF generado: {cert.pdf_url}")
        
        # Enviar email CON PDF ADJUNTADO
        delivery_log = cert.deliver(
            method='email',
            recipient=cert.student.email,
            sent_by=admin
        )
        
        if delivery_log.status == 'success':
            print(f"  ✅ Email enviado a {cert.student.email} - PDF ADJUNTADO\n")
        else:
            print(f"  ⚠️  {delivery_log.error_message}\n")
            
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print("="*80)
print("✅ COMPLETADO")
print("="*80)
