"""
Email Service - Send certificates via email using SendGrid API
"""

import base64
import logging

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    FileContent,
    FileName,
    FileType,
    From,
    Mail,
    To,
)

logger = logging.getLogger(__name__)


class EmailService:
    """Send certificate emails using SendGrid API"""

    @staticmethod
    def _get_client():
        return SendGridAPIClient(settings.SENDGRID_API_KEY)

    @staticmethod
    def send_email(subject, text, recipient_email):
        """
        Send a generic email via SendGrid API.

        Args:
            subject: Email subject
            text: Plain text body
            recipient_email: Email address to send to

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            if not recipient_email:
                return {"success": False, "message": "No email address provided"}

            message = Mail(
                from_email=From(settings.DEFAULT_FROM_EMAIL),
                to_emails=To(recipient_email),
                subject=subject,
                plain_text_content=text,
            )

            client = EmailService._get_client()
            client.send(message)

            logger.info("Email sent to %s: %s", recipient_email, subject)
            return {"success": True, "message": f"Email sent to {recipient_email}"}

        except Exception as e:
            error_msg = str(e)
            logger.error("Error sending email: %s", error_msg)
            return {"success": False, "message": f"Email error: {error_msg}"}

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
                return {"success": False, "message": "No email address provided"}

            subject = f"🎓 Tu Certificado - {certificate.event.name}"

            text = f"""
Hola {certificate.participant.first_name},

Felicidades! Tu certificado del evento "{certificate.event.name}" está listo.

📜 Detalles:
- Evento: {certificate.event.name}
- Fecha: {certificate.event.event_date.strftime('%d/%m/%Y') if certificate.event.event_date else 'No disponible'}
- Código: {certificate.verification_code}
- PDF: {certificate.pdf_url if certificate.pdf_url else 'Pendiente de generar'}

Este certificado expira el: {certificate.expires_at.strftime('%d/%m/%Y') if certificate.expires_at else 'Nunca'}

¡Descárgalo desde el enlace anterior!

Saludos,
Sistema de Certificados
            """

            message = Mail(
                from_email=From(settings.DEFAULT_FROM_EMAIL),
                to_emails=To(recipient_email),
                subject=subject,
                plain_text_content=text,
            )

            if certificate.pdf_url:
                try:
                    filename = certificate.pdf_url.split("/")[-1]
                    pdf_path = settings.CERTIFICATES_PDF_PATH / filename

                    logger.info("Attempting to attach PDF: %s", pdf_path)

                    if pdf_path.exists():
                        with open(pdf_path, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode()

                        attachment = Attachment(
                            FileContent(encoded),
                            FileName(filename),
                            FileType("application/pdf"),
                            Disposition("attachment"),
                        )
                        message.attachment = attachment
                        logger.info("PDF attached successfully: %s", filename)
                    else:
                        logger.warning("PDF file not found at: %s", pdf_path)

                except Exception:
                    logger.exception("Error attaching PDF")

            client = EmailService._get_client()
            response = client.send(message)

            logger.info(
                "Email sent to %s for certificate %s (status_code=%s)",
                recipient_email,
                certificate.id,
                response.status_code,
            )
            return {
                "success": True,
                "message": f"Email sent to {recipient_email}",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error("Error sending email: %s", error_msg)
            return {"success": False, "message": f"Email error: {error_msg}"}

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
            "sent": 0,
            "failed": 0,
            "errors": [],
        }

        for cert in certificates:
            if recipient_map and cert.id in recipient_map:
                recipient = recipient_map[cert.id]
            else:
                recipient = cert.participant.email

            result = EmailService.send_certificate(cert, recipient)

            if result["success"]:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({"certificate_id": str(cert.id), "error": result["message"]})

        return results
