from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from core.helpers import (
    validate_verification_code,
    validate_certificate_status,
    validate_delivery_method,
    format_certificate_status,
    format_delivery_method,
    format_delivery_status,
    format_date,
    calculate_expiration_date,
    is_certificate_expired,
    days_until_expiration,
    format_error_message,
    get_delivery_method_display_icon,
    get_delivery_status_symbol,
)


class ValidateVerificationCodeTest(TestCase):
    def test_valid_code(self):
        self.assertTrue(validate_verification_code('ABCD-1234-EF56-GH78'))

    def test_invalid_code_lowercase(self):
        self.assertFalse(validate_verification_code('abcd-1234-ef56-gh78'))

    def test_invalid_code_missing_segment(self):
        self.assertFalse(validate_verification_code('ABCD-1234-EF56'))

    def test_empty_string(self):
        self.assertFalse(validate_verification_code(''))

    def test_none_value(self):
        self.assertFalse(validate_verification_code(None))


class ValidateCertificateStatusTest(TestCase):
    def test_valid_statuses(self):
        for status in ['pending', 'generated', 'delivered', 'failed']:
            self.assertTrue(validate_certificate_status(status))

    def test_invalid_status(self):
        self.assertFalse(validate_certificate_status('unknown'))

    def test_empty_status(self):
        self.assertFalse(validate_certificate_status(''))


class ValidateDeliveryMethodTest(TestCase):
    def test_valid_methods(self):
        for method in ['email', 'whatsapp', 'link']:
            self.assertTrue(validate_delivery_method(method))

    def test_invalid_method(self):
        self.assertFalse(validate_delivery_method('sms'))


class FormattersTest(TestCase):
    def test_format_certificate_status_known(self):
        self.assertEqual(format_certificate_status('pending'), 'Pendiente')
        self.assertEqual(format_certificate_status('generated'), 'Generado')
        self.assertEqual(format_certificate_status('delivered'), 'Entregado')
        self.assertEqual(format_certificate_status('failed'), 'Fallido')

    def test_format_certificate_status_unknown(self):
        self.assertEqual(format_certificate_status('nope'), 'Desconocido')

    def test_format_delivery_method_known(self):
        self.assertEqual(format_delivery_method('email'), 'Correo Electrónico')
        self.assertEqual(format_delivery_method('whatsapp'), 'WhatsApp')
        self.assertEqual(format_delivery_method('link'), 'Enlace Público')

    def test_format_delivery_status_known(self):
        self.assertEqual(format_delivery_status('pending'), 'Pendiente')
        self.assertEqual(format_delivery_status('success'), 'Exitoso')
        self.assertEqual(format_delivery_status('error'), 'Error')

    def test_format_date_returns_string(self):
        result = format_date(timezone.now())
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_format_date_none_returns_string(self):
        result = format_date(None)
        self.assertIsInstance(result, str)


class ExpirationTest(TestCase):
    def test_calculate_expiration_date_future(self):
        exp = calculate_expiration_date()
        self.assertGreater(exp, timezone.now())

    def test_is_certificate_expired_past(self):
        self.assertTrue(is_certificate_expired(timezone.now() - timedelta(days=1)))

    def test_is_certificate_expired_future(self):
        self.assertFalse(is_certificate_expired(timezone.now() + timedelta(days=1)))

    def test_days_until_expiration_positive(self):
        self.assertGreater(days_until_expiration(timezone.now() + timedelta(days=30)), 0)

    def test_days_until_expiration_negative_when_expired(self):
        self.assertLess(days_until_expiration(timezone.now() - timedelta(days=5)), 0)


class IconsTest(TestCase):
    def test_delivery_method_icons_return_string(self):
        for method in ['email', 'whatsapp', 'link']:
            self.assertIsInstance(get_delivery_method_display_icon(method), str)

    def test_delivery_status_symbols_return_string(self):
        for status in ['success', 'error', 'pending']:
            self.assertIsInstance(get_delivery_status_symbol(status), str)


class FormatErrorMessageTest(TestCase):
    def test_returns_string(self):
        result = format_error_message(ValueError('algo fallo'))
        self.assertIsInstance(result, str)

    def test_includes_context(self):
        result = format_error_message(ValueError('algo fallo'), context='generando PDF')
        self.assertIn('generando PDF', result)


class FormatDateEdgeCasesTest(TestCase):
    def test_format_date_with_object_without_strftime(self):
        result = format_date(12345)
        self.assertEqual(result, '12345')

    def test_is_certificate_expired_none(self):
        self.assertFalse(is_certificate_expired(None))

    def test_days_until_expiration_none(self):
        self.assertEqual(days_until_expiration(None), 0)


class DeliveryQueryHelpersTest(TestCase):
    def setUp(self):
        from users.models import User
        from students.models import Student
        from events.models import Event
        from certificados.models import Template, Certificate
        from deliveries.models import DeliveryLog

        self.user = User.objects.create_user(email='h@test.com', full_name='Helper', password='pass')
        self.student = Student.objects.create(
            document_id='77777', first_name='Pia', last_name='Lima',
            email='pia@test.com', created_by=self.user
        )
        import datetime
        self.event = Event.objects.create(name='Q Event', event_date=datetime.date(2026, 3, 1), created_by=self.user)
        self.template = Template.objects.create(name='T', created_by=self.user)
        self.cert = Certificate.objects.create(
            student=self.student, event=self.event,
            template=self.template, generated_by=self.user,
        )
        self.log = DeliveryLog.objects.create(
            certificate=self.cert, sent_by=self.user,
            delivery_method='email', recipient='pia@test.com', status='success'
        )

    def test_get_recent_deliveries_returns_queryset(self):
        from core.helpers import get_recent_deliveries
        result = get_recent_deliveries(self.cert, days=30)
        self.assertEqual(result.count(), 1)

    def test_get_successful_deliveries_returns_queryset(self):
        from core.helpers import get_successful_deliveries
        result = get_successful_deliveries(self.cert)
        self.assertEqual(result.count(), 1)

    def test_get_failed_deliveries_returns_empty(self):
        from core.helpers import get_failed_deliveries
        result = get_failed_deliveries(self.cert)
        self.assertEqual(result.count(), 0)


class AdminUtilsTest(TestCase):
    def test_active_badge_active_object(self):
        from core.admin_utils import active_badge

        class Obj:
            is_active = True

        result = str(active_badge(Obj()))
        self.assertIn('green', result)
        self.assertIn('Active', result)

    def test_active_badge_inactive_object(self):
        from core.admin_utils import active_badge

        class Obj:
            is_active = False

        result = str(active_badge(Obj()))
        self.assertIn('red', result)
        self.assertIn('Inactive', result)

    def test_color_badge_returns_html_with_color_and_label(self):
        from core.admin_utils import color_badge
        result = str(color_badge('blue', 'TestLabel'))
        self.assertIn('blue', result)
        self.assertIn('TestLabel', result)
