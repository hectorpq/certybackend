"""
Email Service - Send certificates via email using Django SMTP
"""
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Send certificate emails using SMTP/Gmail"""
    
    @staticmethod
    def send_certificate(certificate, recipient_email):
        """
        Send certificate via email to student
        
        Args:
            certificate: Certificate object
            recipient_email: Email address to send to
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            if not recipient_email:
                return {'success': False, 'message': 'No email address provided'}
            
            # Prepare email
            subject = f"🎓 Tu Certificado - {certificate.event.name}"
            
            message = f"""
Hola {certificate.student.first_name},

Felicidades! Tu certificado del evento "{certificate.event.name}" está listo.

📜 Detalles:
- Evento: {certificate.event.name}
- Fecha: {certificate.event.event_date.strftime('%d/%m/%Y')}
- Código: {certificate.verification_code}
- PDF: {certificate.pdf_url}

Este certificado expira el: {certificate.expires_at.strftime('%d/%m/%Y')}

¡Descárgalo desde el enlace anterior!

Saludos,
Sistema de Certificados
            """
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            
            # Attach PDF if available
            if certificate.pdf_url:
                try:
                    # PDF path: /certificates/pdfs/filename.pdf
                    # Extract filename from pdf_url
                    filename = certificate.pdf_url.split('/')[-1]
                    pdf_path = settings.CERTIFICATES_PDF_PATH / filename
                    
                    logger.info(f"Attempting to attach PDF: {pdf_path}")
                    
                    if pdf_path.exists():
                        with open(str(pdf_path), 'rb') as pdf_file:
                            email.attach(
                                filename=filename,
                                content=pdf_file.read(),
                                mimetype='application/pdf'
                            )
                        logger.info(f"PDF attached successfully: {filename}")
                    else:
                        logger.warning(f"PDF file not found at: {pdf_path}")
                        
                except Exception as attach_err:
                    logger.error(f"Error attaching PDF: {attach_err}", exc_info=True)
            
            # Send email
            result = email.send(fail_silently=False)
            
            if result == 1:
                logger.info(f"Email sent to {recipient_email} for certificate {certificate.id}")
                return {
                    'success': True,
                    'message': f'Email sent to {recipient_email}',
                    'timestamp': timezone.now()
                }
            else:
                return {
                    'success': False,
                    'message': 'Email not sent (unknown error)'
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error sending email: {error_msg}")
            return {
                'success': False,
                'message': f'Email error: {error_msg}'
            }
    
    @staticmethod
    def send_bulk_certificates(certificates, recipient_map=None):
        """
        Send certificates in bulk
        
        Args:
            certificates: Queryset of Certificate objects
            recipient_map: Dict mapping certificate.id to email (optional)
            
        Returns:
            dict: {'sent': int, 'failed': int, 'errors': list}
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for cert in certificates:
            # Determine recipient
            if recipient_map and cert.id in recipient_map:
                recipient = recipient_map[cert.id]
            else:
                recipient = cert.student.email
            
            # Send
            result = EmailService.send_certificate(cert, recipient)
            
            if result['success']:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'certificate_id': str(cert.id),
                    'error': result['message']
                })
        
        return results
