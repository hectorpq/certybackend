"""
WhatsApp Service - Send certificates via Meta WhatsApp Cloud API (free tier: 1,000/month)
"""
import requests
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Send certificate messages via WhatsApp using Meta Cloud API"""

    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self):
        self.token = getattr(settings, 'META_WHATSAPP_TOKEN', None)
        self.phone_id = getattr(settings, 'META_WHATSAPP_PHONE_ID', None)

    def _is_configured(self):
        return bool(self.token and self.phone_id)

    def send_certificate(self, certificate, phone_number):
        """
        Send certificate message via WhatsApp

        Args:
            certificate: Certificate object
            phone_number: WhatsApp phone number with country code (e.g. +51999888777)

        Returns:
            dict: {'success': bool, 'message': str}
        """
        if not self._is_configured():
            return {
                'success': False,
                'message': 'WhatsApp no configurado. Agrega META_WHATSAPP_TOKEN y META_WHATSAPP_PHONE_ID en el .env'
            }

        if not phone_number:
            return {'success': False, 'message': 'No se proporcionó número de teléfono'}

        # Limpiar número: quitar +, espacios, guiones
        clean_number = phone_number.replace('+', '').replace(' ', '').replace('-', '')

        participant_name = certificate.participant.first_name
        message_text = (
            f"Hola {participant_name}!\n\n"
            f"Tu certificado del evento \"{certificate.event.name}\" está listo.\n\n"
            f"Detalles:\n"
            f"- Código de verificación: {certificate.verification_code}\n"
            f"- PDF: {certificate.pdf_url if certificate.pdf_url else 'Pendiente de generar'}\n\n"
            f"Sistema de Certificados"
        )

        url = f"{self.BASE_URL}/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "text",
            "text": {"body": message_text}
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()

            if response.status_code == 200 and 'messages' in data:
                logger.info("WhatsApp enviado a %s", phone_number)
                return {
                    'success': True,
                    'message': f'WhatsApp enviado a {phone_number}',
                    'timestamp': timezone.now()
                }
            else:
                error = data.get('error', {}).get('message', 'Error desconocido')
                logger.error("Error Meta WhatsApp API: %s", error)
                return {'success': False, 'message': f'Error WhatsApp: {error}'}

        except Exception as e:
            logger.error("Excepción enviando WhatsApp: %s", e)
            return {'success': False, 'message': f'WhatsApp error: {str(e)}'}

    def send_bulk_certificates(self, certificates, phone_map=None):
        """
        Send certificates via WhatsApp in bulk

        Args:
            certificates: Queryset of Certificate objects
            phone_map: Dict mapping certificate.id to phone number (optional)

        Returns:
            dict: {'sent': int, 'failed': int, 'errors': list}
        """
        results = {'sent': 0, 'failed': 0, 'errors': []}

        for cert in certificates:
            phone = phone_map.get(cert.id) if phone_map else cert.participant.phone
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


_whatsapp_service = None


def get_whatsapp_service():
    """Get or create WhatsApp service instance"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
