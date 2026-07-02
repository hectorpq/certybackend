"""
Email Service - Send certificates via email using Django's SMTP backend
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send certificate emails using Django's SMTP email backend"""

    @staticmethod
    def _send_raw(subject, text, recipient_email, attachment_path=None):
        if not recipient_email:
            return {"success": False, "message": "No email address provided"}

        try:
            from django.core.mail import EmailMessage

            msg = EmailMessage(
                subject=subject,
                body=text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )

            if attachment_path:
                try:
                    with open(str(attachment_path), "rb") as f:
                        msg.attach(
                            filename=str(attachment_path).split("/")[-1],
                            content=f.read(),
                            mimetype="application/pdf",
                        )
                    logger.info("PDF attached: %s", attachment_path)
                except Exception:
                    logger.exception("Error attaching PDF %s", attachment_path)

            msg.send()
            logger.info("Email sent to %s: %s", recipient_email, subject)
            return {"success": True, "message": f"Email sent to {recipient_email}"}

        except Exception as e:
            error_msg = str(e)
            logger.error("Error sending email: %s", error_msg)
            return {"success": False, "message": f"Email error: {error_msg}"}

    @staticmethod
    def send_email(subject, text, recipient_email):
        return EmailService._send_raw(subject, text, recipient_email)

    @staticmethod
    def send_certificate(certificate, recipient_email):
        if not recipient_email:
            return {"success": False, "message": "No email address provided"}

        subject = f"Tu Certificado - {certificate.event.name}"

        text = f"""
Hola {certificate.participant.first_name},

Felicidades! Tu certificado del evento "{certificate.event.name}" esta listo.

Detalles:
- Evento: {certificate.event.name}
- Fecha: {certificate.event.event_date.strftime('%d/%m/%Y') if certificate.event.event_date else 'No disponible'}
- Codigo: {certificate.verification_code}
- PDF: {certificate.pdf_url if certificate.pdf_url else 'Pendiente de generar'}

Este certificado expira el: {certificate.expires_at.strftime('%d/%m/%Y') if certificate.expires_at else 'Nunca'}

Descargalo desde el enlace anterior!

Saludos,
Sistema de Certificados
        """

        pdf_path = None
        if certificate.pdf_url:
            filename = certificate.pdf_url.split("/")[-1]
            pdf_path = settings.CERTIFICATES_PDF_PATH / filename
            if not pdf_path.exists():
                logger.warning("PDF not found at: %s", pdf_path)
                pdf_path = None

        return EmailService._send_raw(subject, text, recipient_email, attachment_path=pdf_path)

    @staticmethod
    def send_bulk_certificates(certificates, recipient_map=None):
        results = {"sent": 0, "failed": 0, "errors": []}

        for cert in certificates:
            recipient = (recipient_map or {}).get(cert.id) or cert.participant.email
            result = EmailService.send_certificate(cert, recipient)

            if result["success"]:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({"certificate_id": str(cert.id), "error": result["message"]})

        return results
