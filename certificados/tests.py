from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from certificados.models import Certificate, Template
from events.models import Enrollment, Event
from participants.models import Participant
from users.models import User


class TemplateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="admin@test.com", full_name="Admin", password="pass")

    def test_str_with_category(self):
        t = Template.objects.create(name="Clasico", category="Cursos", created_by=self.user)
        self.assertIn("Clasico", str(t))
        self.assertIn("Cursos", str(t))

    def test_str_without_category(self):
        t = Template.objects.create(name="Sin Cat", created_by=self.user)
        self.assertEqual(str(t), "Sin Cat")

    def test_is_active_default_true(self):
        t = Template.objects.create(name="T1", created_by=self.user)
        self.assertTrue(t.is_active)

    def test_default_font_values(self):
        t = Template.objects.create(name="T2", created_by=self.user)
        self.assertEqual(t.font_color, "#000000")
        self.assertEqual(t.font_family, "Helvetica")
        self.assertEqual(t.font_size, 24)


class CertificateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="admin@test.com", full_name="Admin", password="pass")
        self.participant = Participant.objects.create(
            document_id="11111",
            first_name="Luis",
            last_name="Gomez",
            email="luis@test.com",
            phone="999000111",
            created_by=self.user,
        )
        self.event = Event.objects.create(name="Taller Test", event_date=date(2026, 1, 1), created_by=self.user)
        self.template = Template.objects.create(name="Base", created_by=self.user)

    def _make_cert(self, status="pending"):
        cert = Certificate(
            participant=self.participant,
            event=self.event,
            template=self.template,
            generated_by=self.user,
            verification_code="",
        )
        cert.save()
        if status != "pending":
            cert.status = status
            Certificate.objects.filter(pk=cert.pk).update(status=status)
            cert.refresh_from_db()
        return cert

    def test_save_auto_generates_verification_code(self):
        cert = self._make_cert()
        self.assertTrue(len(cert.verification_code) > 0)

    def test_str_includes_student_event_status(self):
        cert = self._make_cert()
        s = str(cert)
        self.assertIn("Luis", s)
        self.assertIn("Taller Test", s)
        self.assertIn("pending", s)

    def test_is_expired_false_when_no_expiry(self):
        cert = self._make_cert()
        self.assertFalse(cert.is_expired())

    def test_is_expired_true_when_past(self):
        cert = self._make_cert()
        cert.expires_at = timezone.now() - timedelta(days=1)
        cert.save()
        self.assertTrue(cert.is_expired())

    def test_is_expired_false_when_future(self):
        cert = self._make_cert()
        cert.expires_at = timezone.now() + timedelta(days=365)
        cert.save()
        self.assertFalse(cert.is_expired())

    def test_generate_verification_code_returns_string(self):
        code = Certificate.generate_verification_code("1", 2)
        self.assertIsInstance(code, str)
        self.assertTrue(len(code) > 2)

    def test_get_delivery_history_empty(self):
        cert = self._make_cert()
        self.assertEqual(list(cert.get_delivery_history()), [])

    def test_has_delivery_attempts_false_initially(self):
        cert = self._make_cert()
        self.assertFalse(cert.has_delivery_attempts())

    def test_last_delivery_attempt_none_initially(self):
        cert = self._make_cert()
        self.assertIsNone(cert.last_delivery_attempt)

    def test_delivery_status_returns_cert_status_when_no_deliveries(self):
        cert = self._make_cert()
        self.assertEqual(cert.delivery_status, "pending")

    def test_determine_recipient_email(self):
        cert = self._make_cert()
        self.assertEqual(cert._determine_recipient("email"), "luis@test.com")

    def test_determine_recipient_whatsapp_uses_phone(self):
        cert = self._make_cert()
        self.assertEqual(cert._determine_recipient("whatsapp"), "999000111")

    def test_determine_recipient_whatsapp_returns_none_when_no_phone(self):
        """RN-07: WhatsApp requires phone — no fallback to email."""
        self.participant.phone = ""
        self.participant.save()
        cert = self._make_cert()
        self.assertIsNone(cert._determine_recipient("whatsapp"))

    def test_determine_recipient_link(self):
        cert = self._make_cert()
        self.assertEqual(cert._determine_recipient("link"), "luis@test.com")

    def test_update_delivery_status_success(self):
        cert = self._make_cert()
        log = MagicMock()
        cert._update_delivery_status(log, {"success": True, "message": "ok"})
        self.assertEqual(cert.status, "sent")
        self.assertEqual(log.status, "success")

    def test_update_delivery_status_failure(self):
        cert = self._make_cert()
        log = MagicMock()
        cert._update_delivery_status(log, {"success": False, "message": "error!"})
        self.assertEqual(cert.status, "failed")
        self.assertEqual(log.status, "error")
        self.assertEqual(log.error_message, "error!")

    def test_mark_as_failed_raises_when_pending(self):
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.mark_as_failed("some error")

    def test_mark_as_failed_on_generated_cert(self):
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status="generated")
        cert.refresh_from_db()
        cert.mark_as_failed("PDF error")
        cert.refresh_from_db()
        self.assertEqual(cert.status, "failed")

    def test_generate_raises_if_not_pending(self):
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status="generated")
        cert.refresh_from_db()
        with self.assertRaises(ValidationError):
            cert.generate(skip_attendance_check=True)

    def test_generate_raises_if_student_not_enrolled(self):
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.generate()

    def test_generate_raises_if_student_absent(self):
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=False,
            created_by=self.user,
        )
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.generate()

    @patch("services.pdf_service.PDFService.generate_certificate_pdf")
    def test_generate_success(self, mock_pdf):
        mock_pdf.return_value = {"success": True, "path": "/media/cert.pdf"}
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=True,
            created_by=self.user,
        )
        cert = self._make_cert()
        result = cert.generate(generated_by=self.user, template=self.template)
        self.assertEqual(result.status, "generated")
        self.assertEqual(result.pdf_url, "/media/cert.pdf")

    @patch("services.pdf_service.PDFService.generate_certificate_pdf")
    def test_generate_raises_on_pdf_failure(self, mock_pdf):
        mock_pdf.return_value = {"success": False, "message": "render error"}
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=True,
            created_by=self.user,
        )
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.generate()

    @patch("services.email_service.EmailService.send_certificate")
    def test_deliver_via_email(self, mock_send):
        mock_send.return_value = {"success": True, "message": "sent"}
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status="generated", pdf_url="/media/c.pdf")
        cert.refresh_from_db()
        log = cert.deliver(method="email", sent_by=self.user)
        self.assertEqual(log.status, "success")
        self.assertTrue(cert.has_delivery_attempts())

    def test_deliver_raises_if_not_generated(self):
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.deliver(method="email")

    def test_send_delivery_link_always_succeeds(self):
        cert = self._make_cert()
        cert.pdf_url = "/media/cert.pdf"
        result = cert._send_delivery("link", "luis@test.com")
        self.assertTrue(result["success"])

    def test_send_delivery_unknown_method_raises(self):
        cert = self._make_cert()
        with self.assertRaises(Exception):
            cert._send_delivery("fax", "luis@test.com")

    @patch("services.whatsapp_service.get_whatsapp_service")
    def test_send_delivery_whatsapp_calls_service(self, mock_get):
        mock_ws = MagicMock()
        mock_ws.send_certificate.return_value = {"success": True, "message": "sent"}
        mock_get.return_value = mock_ws
        cert = self._make_cert()
        result = cert._send_delivery("whatsapp", "999000111")
        self.assertTrue(result["success"])

    @patch("services.pdf_service.PDFService.generate_certificate_pdf")
    def test_generate_sets_verification_code_when_empty(self, mock_pdf):
        mock_pdf.return_value = {"success": True, "path": "/media/cert.pdf"}
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=True,
            created_by=self.user,
        )
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(verification_code="")
        cert.refresh_from_db()
        self.assertEqual(cert.verification_code, "")
        result = cert.generate(generated_by=self.user, skip_attendance_check=True)
        self.assertNotEqual(result.verification_code, "")

    def test_deliver_raises_when_no_recipient(self):
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status="generated")
        cert.refresh_from_db()
        with patch.object(cert, "_determine_recipient", return_value=""):
            with self.assertRaises(Exception):
                cert.deliver(method="email")

    def test_send_delivery_whatsapp_module_not_found_returns_failure(self):
        cert = self._make_cert()
        with patch(
            "services.whatsapp_service.get_whatsapp_service",
            side_effect=ModuleNotFoundError("No module"),
        ):
            result = cert._send_delivery("whatsapp", "999000111")
        self.assertFalse(result["success"])
        self.assertIn("not configured", result["message"])


# ─────────────────────────────────────────────
# PASO 2 — Reglas de negocio faltantes
# TC-010, TC-011, TC-017, TC-018, TC-019, TC-020, TC-021
# ─────────────────────────────────────────────


class AttendanceBusinessRuleTest(TestCase):
    """TC-010/011 — attendance=True es requisito para generar certificado."""

    def setUp(self):
        self.user = User.objects.create_user(email="admin2@test.com", full_name="Admin", password="pass")
        self.participant = Participant.objects.create(
            document_id="ATT001",
            first_name="Ana",
            last_name="Torres",
            email="ana@test.com",
            phone="111222333",
            created_by=self.user,
        )
        self.event = Event.objects.create(name="Evento Att", event_date=date(2026, 3, 1), created_by=self.user)

    def test_tc011_generate_blocked_when_attendance_false(self):
        """TC-011: attendance=False debe bloquear la generación."""
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=False,
            created_by=self.user,
        )
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        with self.assertRaises(ValidationError) as ctx:
            cert.generate()
        self.assertIn("attend", str(ctx.exception).lower())

    @patch("services.pdf_service.PDFService.generate_certificate_pdf")
    def test_tc010_generate_succeeds_when_attendance_true(self, mock_pdf):
        """TC-010: attendance=True permite la generación."""
        mock_pdf.return_value = {"success": True, "path": "/media/cert.pdf"}
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=True,
            created_by=self.user,
        )
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        result = cert.generate(generated_by=self.user)
        self.assertEqual(result.status, "generated")

    def test_generate_blocked_when_not_enrolled_at_all(self):
        """Sin matrícula no hay certificado."""
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        with self.assertRaises(ValidationError):
            cert.generate()


class WhatsAppPhoneRequirementTest(TestCase):
    """TC-019/020 — WhatsApp requiere teléfono; no usa email como fallback."""

    def setUp(self):
        self.user = User.objects.create_user(email="admin3@test.com", full_name="Admin", password="pass")
        self.event = Event.objects.create(name="WA Evento", event_date=date(2026, 4, 1), created_by=self.user)

    def _make_cert(self, phone=""):
        participant = Participant.objects.create(
            document_id=f'WA{phone or "NOPH"}',
            first_name="Mario",
            last_name="Ruiz",
            email="mario@test.com",
            phone=phone,
            created_by=self.user,
        )
        return Certificate.objects.create(participant=participant, event=self.event, generated_by=self.user)

    def test_tc020_whatsapp_without_phone_raises_validation_error(self):
        """TC-020: sin teléfono, deliver vía WhatsApp debe fallar con ValidationError."""
        cert = self._make_cert(phone="")
        Certificate.objects.filter(pk=cert.pk).update(status="generated", pdf_url="/media/c.pdf")
        cert.refresh_from_db()
        with self.assertRaises(ValidationError) as ctx:
            cert.deliver(method="whatsapp")
        self.assertIn("whatsapp", str(ctx.exception).lower())

    @patch("services.whatsapp_service.get_whatsapp_service")
    def test_tc019_whatsapp_with_phone_calls_service(self, mock_get):
        """TC-019: con teléfono registrado, WhatsApp llama al servicio."""
        mock_ws = MagicMock()
        mock_ws.send_certificate.return_value = {
            "success": True,
            "message": "sent",
            "sid": "SM123",
        }
        mock_get.return_value = mock_ws
        cert = self._make_cert(phone="999111222")
        Certificate.objects.filter(pk=cert.pk).update(status="generated", pdf_url="/media/c.pdf")
        cert.refresh_from_db()
        log = cert.deliver(method="whatsapp")
        self.assertEqual(log.status, "success")
        mock_ws.send_certificate.assert_called_once()

    def test_determine_recipient_whatsapp_returns_phone_when_set(self):
        cert = self._make_cert(phone="555000999")
        self.assertEqual(cert._determine_recipient("whatsapp"), "555000999")

    def test_determine_recipient_whatsapp_returns_none_when_no_phone(self):
        cert = self._make_cert(phone="")
        self.assertIsNone(cert._determine_recipient("whatsapp"))


class DeliveryRetryTest(TestCase):
    """TC-017/021 — reintento de entrega NO regenera el PDF; crea nuevo DeliveryLog."""

    def setUp(self):
        self.user = User.objects.create_user(email="admin4@test.com", full_name="Admin", password="pass")
        self.participant = Participant.objects.create(
            document_id="RET001",
            first_name="Lucia",
            last_name="Vega",
            email="lucia@test.com",
            phone="777888999",
            created_by=self.user,
        )
        self.event = Event.objects.create(name="Retry Evento", event_date=date(2026, 5, 1), created_by=self.user)
        self.cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        Certificate.objects.filter(pk=self.cert.pk).update(status="failed", pdf_url="/media/original.pdf")
        self.cert.refresh_from_db()

    @patch("services.email_service.EmailService.send_certificate")
    def test_tc017_retry_email_creates_new_delivery_log(self, mock_send):
        """TC-017: reintento email en estado failed crea nuevo log sin regenerar PDF."""
        mock_send.return_value = {"success": True, "message": "resent"}
        original_pdf = self.cert.pdf_url

        log1 = self.cert.deliver(method="email")
        self.cert.refresh_from_db()
        log2 = self.cert.deliver(method="email")

        self.cert.refresh_from_db()
        self.assertEqual(self.cert.pdf_url, original_pdf)
        self.assertEqual(self.cert.deliveries.count(), 2)
        self.assertNotEqual(log1.id, log2.id)

    @patch("services.email_service.EmailService.send_certificate")
    def test_tc018_retry_updates_cert_status_to_sent_on_success(self, mock_send):
        """TC-018: reintento exitoso cambia el estado de failed a sent."""
        mock_send.return_value = {"success": True, "message": "ok"}
        self.cert.deliver(method="email")
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.status, "sent")

    @patch("services.email_service.EmailService.send_certificate")
    def test_retry_failed_delivery_keeps_failed_status(self, mock_send):
        """Reintento fallido mantiene el estado failed."""
        mock_send.return_value = {"success": False, "message": "smtp error"}
        self.cert.deliver(method="email")
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.status, "failed")

    @patch("services.whatsapp_service.get_whatsapp_service")
    def test_tc021_retry_whatsapp_creates_new_delivery_log(self, mock_get):
        """TC-021: reintento WhatsApp en estado failed crea nuevo log sin regenerar PDF."""
        mock_ws = MagicMock()
        mock_ws.send_certificate.return_value = {
            "success": True,
            "message": "sent",
            "sid": "SM999",
        }
        mock_get.return_value = mock_ws
        original_pdf = self.cert.pdf_url

        log1 = self.cert.deliver(method="whatsapp")
        self.cert.refresh_from_db()
        log2 = self.cert.deliver(method="whatsapp")

        self.cert.refresh_from_db()
        self.assertEqual(self.cert.pdf_url, original_pdf)
        self.assertEqual(self.cert.deliveries.count(), 2)
        self.assertNotEqual(log1.id, log2.id)


class CertificateUniqueConstraintTest(TestCase):
    """RN-03/04 — unique_together garantiza un solo certificado por par estudiante+evento."""

    def setUp(self):
        self.user = User.objects.create_user(email="admin5@test.com", full_name="Admin", password="pass")
        self.participant = Participant.objects.create(
            document_id="UNIQ001",
            first_name="Pedro",
            last_name="Mora",
            email="pedro@test.com",
            phone="",
            created_by=self.user,
        )
        self.event = Event.objects.create(name="Unique Evento", event_date=date(2026, 6, 1), created_by=self.user)

    def test_rn04_cannot_create_duplicate_certificate(self):
        """RN-04: un solo certificado por par estudiante+evento."""
        Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        with self.assertRaises(Exception):
            Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)

    def test_get_or_create_returns_existing_not_new(self):
        """get_or_create respeta la restricción unique_together."""
        cert1, created1 = Certificate.objects.get_or_create(
            participant=self.participant,
            event=self.event,
            defaults={"generated_by": self.user},
        )
        cert2, created2 = Certificate.objects.get_or_create(
            participant=self.participant,
            event=self.event,
            defaults={"generated_by": self.user},
        )
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(cert1.id, cert2.id)


class CertificateExpiryTest(TestCase):
    """RN-05 — los certificados vencen a 365 días."""

    def setUp(self):
        self.user = User.objects.create_user(email="admin6@test.com", full_name="Admin", password="pass")
        self.participant = Participant.objects.create(
            document_id="EXP001",
            first_name="Sara",
            last_name="Rios",
            email="sara@test.com",
            phone="111222333",
            created_by=self.user,
        )
        self.event = Event.objects.create(name="Expiry Evento", event_date=date(2026, 7, 1), created_by=self.user)

    @patch("services.pdf_service.PDFService.generate_certificate_pdf")
    def test_rn05_expires_at_set_to_365_days_on_generate(self, mock_pdf):
        """RN-05: expires_at = now + 365 días al generar."""
        mock_pdf.return_value = {"success": True, "path": "/media/cert.pdf"}
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=True,
            created_by=self.user,
        )
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        from datetime import timedelta

        from django.utils import timezone

        before = timezone.now() + timedelta(days=364)
        after = timezone.now() + timedelta(days=366)
        cert.generate(generated_by=self.user)
        self.assertIsNotNone(cert.expires_at)
        self.assertGreater(cert.expires_at, before)
        self.assertLess(cert.expires_at, after)

    def test_is_not_expired_when_no_expires_at(self):
        """Certificado sin expires_at nunca expira."""
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        self.assertFalse(cert.is_expired())


class NoPDFRegenerationGuardTest(TestCase):
    """RN-06 — PDF no se regenera si ya está en generated/sent/failed."""

    def setUp(self):
        self.user = User.objects.create_user(email="admin7@test.com", full_name="Admin", password="pass")
        self.participant = Participant.objects.create(
            document_id="NOREG001",
            first_name="Tomas",
            last_name="Aguilar",
            email="tomas@test.com",
            phone="",
            created_by=self.user,
        )
        self.event = Event.objects.create(name="NoRegen Evento", event_date=date(2026, 8, 1), created_by=self.user)

    def test_rn06_generate_raises_if_status_generated(self):
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        Certificate.objects.filter(pk=cert.pk).update(status="generated")
        cert.refresh_from_db()
        with self.assertRaises(ValidationError) as ctx:
            cert.generate(skip_attendance_check=True)
        self.assertIn("generated", str(ctx.exception))

    def test_rn06_generate_raises_if_status_sent(self):
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        Certificate.objects.filter(pk=cert.pk).update(status="sent")
        cert.refresh_from_db()
        with self.assertRaises(ValidationError) as ctx:
            cert.generate(skip_attendance_check=True)
        self.assertIn("sent", str(ctx.exception))

    def test_rn06_generate_raises_if_status_failed(self):
        cert = Certificate.objects.create(participant=self.participant, event=self.event, generated_by=self.user)
        Certificate.objects.filter(pk=cert.pk).update(status="failed")
        cert.refresh_from_db()
        with self.assertRaises(ValidationError) as ctx:
            cert.generate(skip_attendance_check=True)
        self.assertIn("failed", str(ctx.exception))
