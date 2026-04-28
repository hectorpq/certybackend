"""
Celery tasks for async certificate delivery and PDF generation.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_certificate_email_task(self, certificate_id, recipient_email):
    """Send a single certificate via email asynchronously."""
    try:
        from certificados.models import Certificate
        from services.email_service import EmailService

        cert = Certificate.objects.select_related('participant', 'event').get(pk=certificate_id)
        result = EmailService.send_certificate(cert, recipient_email)
        if not result['success']:
            raise ValueError(result['message'])
        logger.info('Async email sent for certificate %s', certificate_id)
        return result
    except Exception as exc:
        logger.error('Email task failed for cert %s: %s', certificate_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_certificate_pdf_task(self, certificate_id):
    """Generate a PDF for a certificate asynchronously."""
    try:
        from certificados.models import Certificate
        from services.pdf_service import PDFService

        cert = Certificate.objects.select_related(
            'participant', 'event', 'template'
        ).get(pk=certificate_id)
        template = cert.template if cert.template_id else None
        result = PDFService.generate_certificate_pdf(cert, template=template)
        if result['success']:
            cert.pdf_url = result['path']
            cert.save(update_fields=['pdf_url'])
        logger.info('PDF task complete for certificate %s: %s', certificate_id, result)
        return result
    except Exception as exc:
        logger.error('PDF task failed for cert %s: %s', certificate_id, exc)
        raise self.retry(exc=exc)


@shared_task
def send_bulk_certificates_task(event_id, method='email'):
    """Send all certificates for an event asynchronously."""
    from events.models import Enrollment
    from certificados.models import Certificate
    from services.email_service import EmailService

    certificates = Certificate.objects.filter(
        event_id=event_id
    ).select_related('participant', 'event')

    if method == 'email':
        result = EmailService.send_bulk_certificates(list(certificates))
    else:
        result = {'sent': 0, 'failed': 0, 'errors': [f'Method {method} not supported in bulk task']}

    logger.info('Bulk send task for event %s: %s', event_id, result)
    return result
