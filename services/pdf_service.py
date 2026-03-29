"""
PDF Generation Service - Create real PDF certificates using reportlab
"""
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from django.conf import settings
from django.utils import timezone
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFService:
    """Generate real PDF certificates using reportlab"""
    
    BASE_WIDTH, BASE_HEIGHT = landscape(A4)
    PDF_PATH = settings.CERTIFICATES_PDF_PATH
    
    @staticmethod
    def generate_certificate_pdf(certificate, template=None):
        """
        Generate PDF certificate
        
        Args:
            certificate: Certificate object
            template: Template object (optional)
            
        Returns:
            dict: {'success': bool, 'path': str, 'message': str}
        """
        try:
            # Create directory if not exists
            PDFService.PDF_PATH.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{certificate.student.id}_{certificate.event.id}_{certificate.verification_code}.pdf"
            filepath = PDFService.PDF_PATH / filename
            
            # Create canvas
            c = canvas.Canvas(str(filepath), pagesize=landscape(A4))
            
            # Set colors
            color_primary = HexColor('#1e3a8a')  # Blue
            color_secondary = HexColor('#94a3b8')  # Gray
            
            # Background color
            c.setFillColor(HexColor('#f8fafc'))
            c.rect(0, 0, PDFService.BASE_WIDTH, PDFService.BASE_HEIGHT, fill=True, stroke=False)
            
            # Add border
            c.setLineWidth(3)
            c.setStrokeColor(color_primary)
            c.rect(0.3*inch, 0.3*inch, PDFService.BASE_WIDTH - 0.6*inch, PDFService.BASE_HEIGHT - 0.6*inch)
            
            # Title
            c.setFont("Helvetica-Bold", 48)
            c.setFillColor(color_primary)
            c.drawCentredString(PDFService.BASE_WIDTH/2, PDFService.BASE_HEIGHT - 1.5*inch, "CERTIFICADO")
            
            # Subtitle
            c.setFont("Helvetica", 24)
            c.setFillColor(color_secondary)
            c.drawCentredString(PDFService.BASE_WIDTH/2, PDFService.BASE_HEIGHT - 2.2*inch, "DE ASISTENCIA Y PARTICIPACIÓN")
            
            # Student name
            c.setFont("Helvetica-Bold", 28)
            c.setFillColor(color_primary)
            student_name = f"{certificate.student.first_name} {certificate.student.last_name}".upper()
            c.drawCentredString(PDFService.BASE_WIDTH/2, PDFService.BASE_HEIGHT - 3.2*inch, student_name)
            
            # Event info
            c.setFont("Helvetica", 16)
            c.setFillColor(color_secondary)
            
            y_pos = PDFService.BASE_HEIGHT - 4*inch
            c.drawString(1*inch, y_pos, f"Por haber completado exitosamente:")
            
            y_pos -= 0.4*inch
            c.setFont("Helvetica-Bold", 18)
            c.setFillColor(color_primary)
            event_text = certificate.event.name.upper()
            c.drawString(1.5*inch, y_pos, event_text)
            
            y_pos -= 0.5*inch
            c.setFont("Helvetica", 14)
            c.setFillColor(color_secondary)
            c.drawString(1.5*inch, y_pos, f"Realizado el: {certificate.event.event_date.strftime('%d de %B de %Y')}")
            
            # Details section
            y_pos -= 0.8*inch
            c.setFont("Helvetica", 10)
            c.setFillColor(color_secondary)
            
            c.drawString(1*inch, y_pos, f"Código de Verificación: {certificate.verification_code}")
            y_pos -= 0.25*inch
            c.drawString(1*inch, y_pos, f"Válido hasta: {certificate.expires_at.strftime('%d/%m/%Y')}")
            y_pos -= 0.25*inch
            c.drawString(1*inch, y_pos, f"Emitido el: {timezone.now().strftime('%d/%m/%Y a las %H:%M')}")
            
            # Signature area
            y_pos -= 0.8*inch
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(color_primary)
            c.drawString(1*inch, y_pos, "Autorizado por:")
            c.drawString(7*inch, y_pos, "Código QR:")
            
            y_pos -= 0.3*inch
            c.setFont("Helvetica", 10)
            c.setFillColor(color_secondary)
            c.drawString(1*inch, y_pos, "Sistema de Certificación")
            c.drawString(7*inch, y_pos, "[QR Aquí]")
            
            # Footer
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor('#cbd5e1'))
            c.drawString(0.5*inch, 0.3*inch, f"ID: {certificate.id}")
            c.drawCentredString(PDFService.BASE_WIDTH/2, 0.3*inch, "www.certificados.example.com")
            c.drawRightString(PDFService.BASE_WIDTH - 0.5*inch, 0.3*inch, "© 2026")
            
            # Save canvas
            c.save()
            
            logger.info(f"PDF generated: {filepath}")
            
            return {
                'success': True,
                'path': f'/certificates/pdfs/{filename}',
                'filename': filename,
                'message': 'PDF generated successfully'
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating PDF: {error_msg}")
            return {
                'success': False,
                'path': None,
                'message': f'PDF generation error: {error_msg}'
            }
    
    @staticmethod
    def generate_bulk_pdfs(certificates):
        """
        Generate PDFs for multiple certificates
        
        Args:
            certificates: Queryset of Certificate objects
            
        Returns:
            dict: {'generated': int, 'failed': int, 'errors': list}
        """
        results = {
            'generated': 0,
            'failed': 0,
            'errors': []
        }
        
        for cert in certificates:
            result = PDFService.generate_certificate_pdf(cert)
            
            if result['success']:
                cert.pdf_url = result['path']
                cert.save()
                results['generated'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'certificate_id': str(cert.id),
                    'error': result['message']
                })
        
        return results
