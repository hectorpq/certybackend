"""
PDF Generation Service - Create real PDF certificates using reportlab
"""
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
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
        Generate PDF certificate using template background and layout config
        
        Args:
            certificate: Certificate object
            template: Template object (optional)
            
        Returns:
            dict: {'success': bool, 'path': str, 'message': str}
        """
        try:
            PDFService.PDF_PATH.mkdir(parents=True, exist_ok=True)
            
            filename = f"{certificate.student.id}_{certificate.event.id}_{certificate.verification_code}.pdf"
            filepath = PDFService.PDF_PATH / filename
            
            c = canvas.Canvas(str(filepath), pagesize=landscape(A4))
            
            if template and template.background_image:
                try:
                    img_path = template.background_image.path
                    c.drawImage(ImageReader(img_path), 0, 0, width=PDFService.BASE_WIDTH, height=PDFService.BASE_HEIGHT)
                except Exception as e:
                    logger.warning("Could not load template background: %s", e)
                    PDFService._draw_default_background(c)
            else:
                PDFService._draw_default_background(c)
            
            layout = template.layout_config if template else {}
            
            student_name = f"{certificate.student.first_name} {certificate.student.last_name}".upper()
            event_name = certificate.event.name.upper()
            event_date = certificate.event.event_date.strftime('%d de %B de %Y')
            verification_code = certificate.verification_code
            expires_at = certificate.expires_at.strftime('%d/%m/%Y') if certificate.expires_at else 'N/A'
            
            student_config = layout.get('student_name', {})
            PDFService._draw_text(c, student_name, student_config, PDFService.BASE_WIDTH / 2, PDFService.BASE_HEIGHT - 3.2*inch, 28, color_primary=HexColor('#1e3a8a'))
            
            event_config = layout.get('event_name', {})
            PDFService._draw_text(c, event_name, event_config, 1.5*inch, PDFService.BASE_HEIGHT - 4*inch, 18, color_primary=HexColor('#1e3a8a'))
            
            date_config = layout.get('event_date', {})
            PDFService._draw_text(c, f"Realizado el: {event_date}", date_config, 1.5*inch, PDFService.BASE_HEIGHT - 4.5*inch, 14, color_primary=HexColor('#94a3b8'))
            
            code_config = layout.get('verification_code', {})
            PDFService._draw_text(c, f"Código: {verification_code}", code_config, 1*inch, 2*inch, 10, color_primary=HexColor('#64748b'))
            PDFService._draw_text(c, f"Válido hasta: {expires_at}", {}, 1*inch, 1.7*inch, 10, color_primary=HexColor('#64748b'))
            
            c.save()
            
            logger.info("PDF generated: %s", filepath)
            
            return {
                'success': True,
                'path': f'/certificates/pdfs/{filename}',
                'filename': filename,
                'message': 'PDF generated successfully'
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error("Error generating PDF: %s", error_msg)
            return {
                'success': False,
                'path': None,
                'message': f'PDF generation error: {error_msg}'
            }
    
    @staticmethod
    def _draw_default_background(c):
        color_primary = HexColor('#1e3a8a')
        color_secondary = HexColor('#94a3b8')
        
        c.setFillColor(HexColor('#f8fafc'))
        c.rect(0, 0, PDFService.BASE_WIDTH, PDFService.BASE_HEIGHT, fill=True, stroke=False)
        
        c.setLineWidth(3)
        c.setStrokeColor(color_primary)
        c.rect(0.3*inch, 0.3*inch, PDFService.BASE_WIDTH - 0.6*inch, PDFService.BASE_HEIGHT - 0.6*inch)
        
        c.setFont("Helvetica-Bold", 48)
        c.setFillColor(color_primary)
        c.drawCentredString(PDFService.BASE_WIDTH/2, PDFService.BASE_HEIGHT - 1.5*inch, "CERTIFICADO")
        
        c.setFont("Helvetica", 24)
        c.setFillColor(color_secondary)
        c.drawCentredString(PDFService.BASE_WIDTH/2, PDFService.BASE_HEIGHT - 2.2*inch, "DE ASISTENCIA Y PARTICIPACIÓN")
    
    @staticmethod
    def _draw_text(c, text, config, default_x, default_y, default_size, color_primary=None):
        x = config.get('x', default_x / inch) * inch if isinstance(config.get('x'), (int, float)) else default_x
        y = config.get('y', default_y / inch) * inch if isinstance(config.get('y'), (int, float)) else default_y
        font_size = config.get('font_size', default_size)
        font_family = config.get('font_family', 'Helvetica')
        color = config.get('color', '#000000')
        
        centered = config.get('centered', False)

        c.setFont(f"{font_family}-Bold" if 'Bold' not in font_family else font_family, font_size)
        c.setFillColor(HexColor(color) if color_primary is None else color_primary)

        if centered or (isinstance(x, (int, float)) and x > PDFService.BASE_WIDTH / 2):
            c.drawCentredString(x, y, text)
        else:
            c.drawString(x, y, text)
    
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
            template = cert.template if cert.template_id else None
            result = PDFService.generate_certificate_pdf(cert, template)
            
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