"""
WhatsApp Service - Send certificates via WhatsApp using Twilio API
"""
from twilio.rest import Client
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Send certificate messages via WhatsApp using Twilio"""
    
    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_PHONE_NUMBER
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
    
    def send_certificate(self, certificate, phone_number):
        """
        Send certificate message via WhatsApp
        
        Args:
            certificate: Certificate object
            phone_number: WhatsApp phone number (with country code, e.g. +57...)
            
        Returns:
            dict: {'success': bool, 'message': str, 'sid': str}
        """
        try:
            # Validate Twilio configuration
            if not self.client:
                return {
                    'success': False,
                    'message': 'Twilio not configured. Check TWILIO_ACCOUNT_SID, AUTH_TOKEN, and PHONE_NUMBER in .env',
                    'sid': None
                }
            
            if not phone_number:
                return {
                    'success': False,
                    'message': 'No phone number provided',
                    'sid': None
                }
            
            # Ensure phone number has correct format
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number
            
            # Prepare message
            message_text = f"""
🎓 ¡Hola {certificate.student.first_name}!

Tu certificado del evento "{certificate.event.name}" está listo.

📜 Detalles:
- Código: {certificate.verification_code}
- PDF: {certificate.pdf_url}
- Válido hasta: {certificate.expires_at.strftime('%d/%m/%Y')}

¡Descárgalo desde el enlace!

Sistema de Certificados
            """.strip()
            
            # Send via WhatsApp
            message = self.client.messages.create(
                from_=f"whatsapp:{self.from_number}",
                body=message_text,
                to=f"whatsapp:{phone_number}"
            )
            
            logger.info("WhatsApp message sent to %s, SID: %s", phone_number, message.sid)
            
            return {
                'success': True,
                'message': f'WhatsApp message sent to {phone_number}',
                'sid': message.sid,
                'timestamp': timezone.now()
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error("Error sending WhatsApp: %s", error_msg)
            return {
                'success': False,
                'message': f'WhatsApp error: {error_msg}',
                'sid': None
            }
    
    def send_bulk_certificates(self, certificates, phone_map=None):
        """
        Send certificates via WhatsApp in bulk
        
        Args:
            certificates: Queryset of Certificate objects
            phone_map: Dict mapping certificate.id to phone number (optional)
            
        Returns:
            dict: {'sent': int, 'failed': int, 'errors': list}
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for cert in certificates:
            # Determine phone number
            if phone_map and cert.id in phone_map:
                phone = phone_map[cert.id]
            else:
                phone = cert.student.phone
            
            # Send
            result = self.send_certificate(cert, phone)
            
            if result['success']:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'certificate_id': str(cert.id),
                    'phone': phone,
                    'error': result['message']
                })
        
        return results


# Singleton instance
_whatsapp_service = None

def get_whatsapp_service():
    """Get or create WhatsApp service instance"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
