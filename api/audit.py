"""
Thin helper for writing AuditLog entries.
Import and call log_action() from views; exceptions are silenced so
audit failures never break the main request flow.
"""
import logging

logger = logging.getLogger(__name__)


def log_action(action, *, user=None, certificate=None, ip_address=None, **details):
    """
    Persist an AuditLog entry.

    Args:
        action:      One of AuditLog.ACTION_CHOICES keys.
        user:        User instance (optional).
        certificate: Certificate instance (optional).
        ip_address:  String IP (optional).
        **details:   Arbitrary extra context stored in the JSON `details` field.
    """
    try:
        from api.models import AuditLog
        AuditLog.objects.create(
            action=action,
            user=user,
            certificate=certificate,
            ip_address=ip_address,
            details=details,
        )
    except Exception as exc:
        logger.warning('AuditLog write failed: %s', exc)


def get_client_ip(request):
    """Extract the real client IP, respecting X-Forwarded-For."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None
