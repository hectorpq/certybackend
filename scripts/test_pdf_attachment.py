"""
Test script para verificar PDF attachment en emails
"""
import os
from pathlib import Path
from django.conf import settings
from certificados.models import Certificate
from users.models import User
from services.email_service import EmailService
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("TEST - PDF Attachment en Emails")
print("="*80)

# ============================================================================
# 1. Verificar directorio de PDFs
# ============================================================================
print("\n[1] Verificando directorio de PDFs...")
pdf_path = settings.CERTIFICATES_PDF_PATH
print(f"Path configurado: {pdf_path}")
print(f"¿Existe?: {pdf_path.exists()}")

if pdf_path.exists():
    files = list(pdf_path.glob("*.pdf"))
    print(f"PDFs encontrados: {len(files)}")
    for f in files[:5]:  # Mostrar primeros 5
        size = f.stat().st_size / 1024  # KB
        print(f"  - {f.name} ({size:.1f} KB)")
else:
    print("❌ Directorio no existe!")

# ============================================================================
# 2. Obtener certificado con PDF
# ============================================================================
print("\n[2] Buscando certificado con PDF...")

cert = Certificate.objects.filter(status__in=['generated', 'sent']).first()

if not cert:
    print("❌ No hay certificados generados")
    exit()

print(f"✓ Certificado encontrado:")
print(f"  ID: {cert.id}")
print(f"  Estudiante: {cert.student.first_name} {cert.student.last_name}")
print(f"  Email: {cert.student.email}")
print(f"  PDF URL: {cert.pdf_url}")
print(f"  Status: {cert.status}")

# ============================================================================
# 3. Verificar PDF existe
# ============================================================================
print("\n[3] Verificando PDF en disco...")

if cert.pdf_url:
    filename = cert.pdf_url.split('/')[-1]
    pdf_full_path = settings.CERTIFICATES_PDF_PATH / filename
    
    print(f"Filename: {filename}")
    print(f"Path construida: {pdf_full_path}")
    print(f"¿Existe?: {pdf_full_path.exists()}")
    
    if pdf_full_path.exists():
        size = pdf_full_path.stat().st_size / 1024
        print(f"✓ Tamaño: {size:.1f} KB")
    else:
        print("❌ PDF NO EXISTE EN DISCO")
        print("\nPDFs disponibles:")
        for f in settings.CERTIFICATES_PDF_PATH.glob("*.pdf"):
            print(f"  {f.name}")
else:
    print("❌ Certificado sin PDF URL")

# ============================================================================
# 4. Testear envío de email con PDF
# ============================================================================
print("\n[4] Testeando envío de email con PDF...")

admin = User.objects.filter(is_superuser=True).first()

try:
    result = EmailService.send_certificate(cert, cert.student.email)
    
    print(f"Resultado: {result}")
    
    if result['success']:
        print(f"✅ Email enviado: {result['message']}")
        print(f"\n📧 Revisa tu inbox (incluído spam)")
        print(f"   Destinatario: {cert.student.email}")
        print(f"   PDF adjunto: Debería estar ahí")
    else:
        print(f"❌ Error: {result['message']}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETADO")
print("="*80)
