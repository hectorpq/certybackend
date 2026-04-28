"""
Email Service - Send certificates via email using Django SMTP
"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

logger = logging.getLogger(__name__)

GMAIL_DAILY_LIMIT = 500
GMAIL_WARNING_THRESHOLD = 400


def get_emails_sent_today():
    """Count successful emails sent today via DeliveryLog."""
    from deliveries.models import DeliveryLog

    today = timezone.now().date()
    return DeliveryLog.objects.filter(
        delivery_method="email", status="success", sent_at__date=today
    ).count()


def check_email_limit():
    """
    Returns a dict with the current email usage status.
    {'count': int, 'limit': int, 'warning': bool, 'blocked': bool, 'message': str}
    """
    count = get_emails_sent_today()
    if count >= GMAIL_DAILY_LIMIT:
        return {
            "count": count,
            "limit": GMAIL_DAILY_LIMIT,
            "warning": True,
            "blocked": True,
            "message": f"Límite diario de Gmail alcanzado ({count}/{GMAIL_DAILY_LIMIT}). No se pueden enviar más emails hoy. Se reinicia mañana.",
        }
    if count >= GMAIL_WARNING_THRESHOLD:
        remaining = GMAIL_DAILY_LIMIT - count
        return {
            "count": count,
            "limit": GMAIL_DAILY_LIMIT,
            "warning": True,
            "blocked": False,
            "message": f"Atención: solo quedan {remaining} emails disponibles hoy ({count}/{GMAIL_DAILY_LIMIT}).",
        }
    return {
        "count": count,
        "limit": GMAIL_DAILY_LIMIT,
        "warning": False,
        "blocked": False,
        "message": None,
    }


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
                return {"success": False, "message": "No email address provided"}

            limit_status = check_email_limit()
            if limit_status["blocked"]:
                return {
                    "success": False,
                    "message": limit_status["message"],
                    "email_limit_reached": True,
                }

            # Prepare email
            subject = f"🎓 Tu Certificado - {certificate.event.name}"

            message = f"""
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

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )

            # Attach PDF if available
            if certificate.pdf_url:
                try:
                    # PDF path: /certificates/pdfs/filename.pdf
                    # Extract filename from pdf_url
                    filename = certificate.pdf_url.split("/")[-1]
                    pdf_path = settings.CERTIFICATES_PDF_PATH / filename

                    logger.info("Attempting to attach PDF: %s", pdf_path)

                    if pdf_path.exists():
                        with open(str(pdf_path), "rb") as pdf_file:
                            email.attach(
                                filename=filename,
                                content=pdf_file.read(),
                                mimetype="application/pdf",
                            )
                        logger.info("PDF attached successfully: %s", filename)
                    else:
                        logger.warning("PDF file not found at: %s", pdf_path)

                except Exception as attach_err:
                    logger.error("Error attaching PDF: %s", attach_err, exc_info=True)

            # Send email
            result = email.send(fail_silently=False)

            if result == 1:
                logger.info(
                    "Email sent to %s for certificate %s",
                    recipient_email,
                    certificate.id,
                )
                return {
                    "success": True,
                    "message": f"Email sent to {recipient_email}",
                    "timestamp": timezone.now(),
                }
            else:
                return {"success": False, "message": "Email not sent (unknown error)"}

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
        limit_status = check_email_limit()
        results = {
            "sent": 0,
            "failed": 0,
            "errors": [],
            "email_limit_warning": limit_status["warning"],
            "email_limit_message": limit_status["message"],
        }

        if limit_status["blocked"]:
            return results

        for cert in certificates:
            # Determine recipient
            if recipient_map and cert.id in recipient_map:
                recipient = recipient_map[cert.id]
            else:
                recipient = cert.participant.email

            # Send
            result = EmailService.send_certificate(cert, recipient)

            if result["success"]:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    {"certificate_id": str(cert.id), "error": result["message"]}
                )

        return results
