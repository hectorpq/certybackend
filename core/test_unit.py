from datetime import timedelta

import pytest
from django.test import SimpleTestCase
from django.utils import timezone

from core.helpers import (
    calculate_expiration_date,
    days_until_expiration,
    format_certificate_status,
    format_date,
    format_delivery_method,
    format_delivery_status,
    format_error_message,
    get_delivery_method_display_icon,
    get_delivery_status_symbol,
    is_certificate_expired,
    validate_certificate_status,
    validate_delivery_method,
    validate_verification_code,
)


@pytest.mark.unit
class ValidateVerificationCodeTest(SimpleTestCase):
    def test_valid_code(self):
        self.assertTrue(validate_verification_code("ABCD-1234-EF56-GH78"))

    def test_invalid_code_lowercase(self):
        self.assertFalse(validate_verification_code("abcd-1234-ef56-gh78"))

    def test_invalid_code_missing_segment(self):
        self.assertFalse(validate_verification_code("ABCD-1234-EF56"))

    def test_empty_string(self):
        self.assertFalse(validate_verification_code(""))

    def test_none_value(self):
        self.assertFalse(validate_verification_code(None))


@pytest.mark.unit
class ValidateCertificateStatusTest(SimpleTestCase):
    def test_valid_statuses(self):
        for status in ["pending", "generated", "delivered", "failed"]:
            self.assertTrue(validate_certificate_status(status))

    def test_invalid_status(self):
        self.assertFalse(validate_certificate_status("unknown"))

    def test_empty_status(self):
        self.assertFalse(validate_certificate_status(""))


@pytest.mark.unit
class ValidateDeliveryMethodTest(SimpleTestCase):
    def test_valid_methods(self):
        for method in ["email", "whatsapp", "link"]:
            self.assertTrue(validate_delivery_method(method))

    def test_invalid_method(self):
        self.assertFalse(validate_delivery_method("sms"))


@pytest.mark.unit
class FormattersTest(SimpleTestCase):
    def test_format_certificate_status_known(self):
        self.assertEqual(format_certificate_status("pending"), "Pendiente")
        self.assertEqual(format_certificate_status("generated"), "Generado")
        self.assertEqual(format_certificate_status("delivered"), "Entregado")
        self.assertEqual(format_certificate_status("failed"), "Fallido")

    def test_format_certificate_status_unknown(self):
        self.assertEqual(format_certificate_status("nope"), "Desconocido")

    def test_format_delivery_method_known(self):
        self.assertEqual(format_delivery_method("email"), "Correo Electrónico")
        self.assertEqual(format_delivery_method("whatsapp"), "WhatsApp")
        self.assertEqual(format_delivery_method("link"), "Enlace Público")

    def test_format_delivery_status_known(self):
        self.assertEqual(format_delivery_status("pending"), "Pendiente")
        self.assertEqual(format_delivery_status("success"), "Exitoso")
        self.assertEqual(format_delivery_status("error"), "Error")

    def test_format_date_returns_string(self):
        result = format_date(timezone.now())
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_format_date_none_returns_string(self):
        result = format_date(None)
        self.assertIsInstance(result, str)


@pytest.mark.unit
class ExpirationTest(SimpleTestCase):
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


@pytest.mark.unit
class IconsTest(SimpleTestCase):
    def test_delivery_method_icons_return_string(self):
        for method in ["email", "whatsapp", "link"]:
            self.assertIsInstance(get_delivery_method_display_icon(method), str)

    def test_delivery_status_symbols_return_string(self):
        for status in ["success", "error", "pending"]:
            self.assertIsInstance(get_delivery_status_symbol(status), str)


@pytest.mark.unit
class FormatErrorMessageTest(SimpleTestCase):
    def test_returns_string(self):
        result = format_error_message(ValueError("algo fallo"))
        self.assertIsInstance(result, str)

    def test_includes_context(self):
        result = format_error_message(ValueError("algo fallo"), context="generando PDF")
        self.assertIn("generando PDF", result)


@pytest.mark.unit
class FormatDateEdgeCasesTest(SimpleTestCase):
    def test_format_date_with_object_without_strftime(self):
        result = format_date(12345)
        self.assertEqual(result, "12345")

    def test_is_certificate_expired_none(self):
        self.assertFalse(is_certificate_expired(None))

    def test_days_until_expiration_none(self):
        self.assertEqual(days_until_expiration(None), 0)


@pytest.mark.unit
class AdminUtilsTest(SimpleTestCase):
    def test_active_badge_active_object(self):
        from core.admin_utils import active_badge

        class Obj:
            is_active = True

        result = str(active_badge(Obj()))
        self.assertIn("green", result)
        self.assertIn("Active", result)

    def test_active_badge_inactive_object(self):
        from core.admin_utils import active_badge

        class Obj:
            is_active = False

        result = str(active_badge(Obj()))
        self.assertIn("red", result)
        self.assertIn("Inactive", result)

    def test_color_badge_returns_html_with_color_and_label(self):
        from core.admin_utils import color_badge

        result = str(color_badge("blue", "TestLabel"))
        self.assertIn("blue", result)
        self.assertIn("TestLabel", result)
