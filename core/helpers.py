"""
Helper utilities and constants for the certificate system
"""
import re
from django.utils import timezone
from datetime import timedelta

# ============================================================================
# CONSTANTS
# ============================================================================

CERTIFICATE_VALIDITY_DAYS = 365
VERIFICATION_CODE_FORMAT = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'

CERTIFICATE_STATUS_CHOICES = [
    ('pending', 'Pendiente'),
    ('generated', 'Generado'),
    ('delivered', 'Entregado'),
    ('failed', 'Fallido'),
]

DELIVERY_METHOD_CHOICES = [
    ('email', 'Correo Electrónico'),
    ('whatsapp', 'WhatsApp'),
    ('link', 'Enlace Público'),
]

DELIVERY_STATUS_CHOICES = [
    ('pending', 'Pendiente'),
    ('success', 'Exitoso'),
    ('error', 'Error'),
]


# ============================================================================
# VALIDATORS
# ============================================================================

def validate_verification_code(code) -> bool:
    """
    Validate verification code format (XXXX-XXXX-XXXX-XXXX)
    
    Args:
        code (str): Verification code to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not code:
        return False
    
    return bool(re.match(VERIFICATION_CODE_FORMAT, code))


def validate_certificate_status(status: str) -> bool:
    """
    Validate certificate status
    
    Args:
        status (str): Status to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    valid_statuses = [choice[0] for choice in CERTIFICATE_STATUS_CHOICES]
    return status in valid_statuses


def validate_delivery_method(method: str) -> bool:
    """
    Validate delivery method
    
    Args:
        method (str): Method to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    valid_methods = [choice[0] for choice in DELIVERY_METHOD_CHOICES]
    return method in valid_methods


# ============================================================================
# FORMATTERS
# ============================================================================

def format_certificate_status(status: str) -> str:
    """
    Get human-readable certificate status
    
    Args:
        status (str): Status code
    
    Returns:
        str: Formatted status
    """
    status_map = dict(CERTIFICATE_STATUS_CHOICES)
    return status_map.get(status, 'Desconocido')


def format_delivery_method(method: str) -> str:
    """
    Get human-readable delivery method
    
    Args:
        method (str): Method code
    
    Returns:
        str: Formatted method
    """
    method_map = dict(DELIVERY_METHOD_CHOICES)
    return method_map.get(method, 'Desconocido')


def format_delivery_status(status: str) -> str:
    """
    Get human-readable delivery status
    
    Args:
        status (str): Status code
    
    Returns:
        str: Formatted status
    """
    status_map = dict(DELIVERY_STATUS_CHOICES)
    return status_map.get(status, 'Desconocido')


def format_date(date) -> str:
    """
    Format date to readable string
    
    Args:
        date: Date to format
    
    Returns:
        str: Formatted date (YYYY-MM-DD HH:MM:SS)
    """
    if not date:
        return 'N/A'
    
    if hasattr(date, 'strftime'):
        return date.strftime('%Y-%m-%d %H:%M:%S')
    
    return str(date)


# ============================================================================
# CERTIFICATE HELPERS
# ============================================================================

def calculate_expiration_date(issued_date=None) -> timezone.datetime:
    """
    Calculate certificate expiration date
    
    Args:
        issued_date: Issue date (defaults to now)
    
    Returns:
        datetime: Expiration date
    """
    if issued_date is None:
        issued_date = timezone.now()
    
    return issued_date + timedelta(days=CERTIFICATE_VALIDITY_DAYS)


def is_certificate_expired(expires_at) -> bool:
    """
    Check if certificate is expired
    
    Args:
        expires_at: Expiration datetime
    
    Returns:
        bool: True if expired, False otherwise
    """
    if not expires_at:
        return False
    
    return timezone.now() > expires_at


def days_until_expiration(expires_at) -> int:
    """
    Calculate days until certificate expires
    
    Args:
        expires_at: Expiration datetime
    
    Returns:
        int: Days remaining (negative if already expired)
    """
    if not expires_at:
        return 0
    
    delta = expires_at - timezone.now()
    return delta.days


# ============================================================================
# DELIVERY HELPERS
# ============================================================================

def format_error_message(error: Exception, context: str = '') -> str:
    """
    Format error message for delivery logs
    
    Args:
        error: Exception object
        context: Additional context
    
    Returns:
        str: Formatted error message
    """
    error_str = str(error)
    
    if context:
        return f"[{context}] {error_str}"
    
    return error_str


def get_delivery_method_display_icon(method: str) -> str:
    """
    Get emoji/icon for delivery method
    
    Args:
        method: Delivery method
    
    Returns:
        str: Icon representation
    """
    icons = {
        'email': '📧',
        'whatsapp': '💬',
        'link': '🔗',
    }
    return icons.get(method, '?')


def get_delivery_status_symbol(status: str) -> str:
    """
    Get symbol for delivery status
    
    Args:
        status: Delivery status
    
    Returns:
        str: Status symbol
    """
    symbols = {
        'success': '✓',
        'error': '✗',
        'pending': '⏳',
    }
    return symbols.get(status, '?')


# ============================================================================
# QUERY HELPERS
# ============================================================================

def get_recent_deliveries(certificate, days: int = 30):
    """
    Get recent delivery attempts for a certificate
    
    Args:
        certificate: Certificate object
        days: Number of days to look back
    
    Returns:
        QuerySet: Recent DeliveryLog records
    """
    from django.utils import timezone
    from datetime import timedelta
    from deliveries.models import DeliveryLog
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    return DeliveryLog.objects.filter(
        certificate=certificate,
        sent_at__gte=cutoff_date
    ).order_by('-sent_at')


def get_successful_deliveries(certificate):
    """
    Get successful delivery attempts for a certificate
    
    Args:
        certificate: Certificate object
    
    Returns:
        QuerySet: Successful DeliveryLog records
    """
    from deliveries.models import DeliveryLog
    
    return DeliveryLog.objects.filter(
        certificate=certificate,
        status='success'
    ).order_by('-sent_at')


def get_failed_deliveries(certificate):
    """
    Get failed delivery attempts for a certificate
    
    Args:
        certificate: Certificate object
    
    Returns:
        QuerySet: Failed DeliveryLog records
    """
    from deliveries.models import DeliveryLog
    
    return DeliveryLog.objects.filter(
        certificate=certificate,
        status='error'
    ).order_by('-sent_at')
