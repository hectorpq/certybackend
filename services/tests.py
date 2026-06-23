import io
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase

from certificados.models import Certificate, Template
from events.models import Event
from instructors.models import Instructor
from participants.models import Participant
from services.email_service import EmailService
from services.pdf_service import PDFService
from users.models import User


def make_admin(email="admin@test.com"):
    return User.objects.create_user(email=email, full_name="Admin", password="pass")


def make_cert(user=None, with_instructor=False, doc_id="11111", p_email="luis@test.com"):
    user = user or make_admin()
    participant = Participant.objects.create(
        document_id=doc_id,
        first_name="Luis",
        last_name="Gomez",
        email=p_email,
        phone="999000111",
        created_by=user,
    )
    instructor = None
    if with_instructor:
        instructor = Instructor.objects.create(
            full_name="Dr. Ana Torres",
            email="ana@inst.com",
            specialty="Ingeniería de Software",
            created_by=user,
        )
    event = Event.objects.create(
        name="Workshop",
        event_date=date(2026, 6, 1),
        created_by=user,
        instructor=instructor,
    )
    template = Template.objects.create(name="Base", created_by=user)
    cert = Certificate.objects.create(
        participant=participant,
        event=event,
        template=template,
        generated_by=user,
    )
    return cert, user


# ─────────────────────────────────────────────
# EmailService
# ─────────────────────────────────────────────


@pytest.mark.integration
class EmailServiceTest(TestCase):
    def setUp(self):
        self.cert, self.user = make_cert()

    def test_send_no_recipient_returns_failure(self):
        result = EmailService.send_certificate(self.cert, "")
        self.assertFalse(result["success"])
        self.assertIn("No email", result["message"])

    @patch("django.core.mail.EmailMessage")
    def test_send_certificate_success(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg
        result = EmailService.send_certificate(self.cert, "test@test.com")
        self.assertTrue(result["success"])

    @patch("django.core.mail.EmailMessage")
    def test_send_certificate_exception_returns_failure(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_msg.send.side_effect = Exception("SMTP error")
        mock_email_cls.return_value = mock_msg
        result = EmailService.send_certificate(self.cert, "test@test.com")
        self.assertFalse(result["success"])
        self.assertIn("SMTP error", result["message"])

    @patch("django.core.mail.EmailMessage")
    def test_send_bulk_all_success(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg
        result = EmailService.send_bulk_certificates([self.cert])
        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["failed"], 0)

    @patch("django.core.mail.EmailMessage")
    def test_send_bulk_with_recipient_map(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg
        result = EmailService.send_bulk_certificates([self.cert], recipient_map={self.cert.id: "custom@test.com"})
        self.assertEqual(result["sent"], 1)

    @patch("django.core.mail.EmailMessage")
    def test_send_bulk_failure_logged(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_msg.send.side_effect = Exception("SMTP error")
        mock_email_cls.return_value = mock_msg
        result = EmailService.send_bulk_certificates([self.cert])
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(result["errors"]), 1)

    @patch("django.core.mail.EmailMessage")
    def test_send_certificate_attaches_pdf_when_present(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg
        self.cert.pdf_url = "/media/certificates/cert.pdf"
        self.cert.save()
        with patch("pathlib.Path.exists", return_value=True):
            result = EmailService.send_certificate(self.cert, "test@test.com")
        self.assertTrue(result["success"])

    @patch("django.core.mail.EmailMessage")
    def test_send_certificate_pdf_not_on_disk_logs_warning(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg
        self.cert.pdf_url = "/media/certificates/missing.pdf"
        self.cert.save()
        with patch("pathlib.Path.exists", return_value=False):
            result = EmailService.send_certificate(self.cert, "test@test.com")
        self.assertTrue(result["success"])

    @patch("django.core.mail.EmailMessage")
    def test_send_certificate_pdf_attach_exception_continues(self, mock_email_cls):
        mock_msg = MagicMock()
        mock_email_cls.return_value = mock_msg
        self.cert.pdf_url = "/media/certificates/cert.pdf"
        self.cert.save()
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.WindowsPath.open", side_effect=IOError("disk error")):
                result = EmailService.send_certificate(self.cert, "test@test.com")
        self.assertTrue(result["success"])


# ─────────────────────────────────────────────
# PDFService — core generation
# ─────────────────────────────────────────────


@pytest.mark.integration
class PDFServiceTest(TestCase):
    def setUp(self):
        self.cert, self.user = make_cert()

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_success_no_template(self, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        result = PDFService.generate_certificate_pdf(self.cert, template=None)
        self.assertTrue(result["success"])
        self.assertIn("path", result)

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_with_template_no_bg(self, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        template = Template.objects.create(name="T2", created_by=self.user)
        result = PDFService.generate_certificate_pdf(self.cert, template=template)
        self.assertTrue(result["success"])

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_canvas_exception(self, mock_mkdir, mock_canvas):
        mock_canvas.side_effect = Exception("canvas error")
        result = PDFService.generate_certificate_pdf(self.cert)
        self.assertFalse(result["success"])
        self.assertIn("canvas error", result["message"])

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_bulk_pdfs(self, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        results = PDFService.generate_bulk_pdfs([self.cert])
        self.assertIn("generated", results)
        self.assertIn("failed", results)

    @patch("services.pdf_service.PDFService.generate_certificate_pdf")
    def test_generate_bulk_pdfs_failure_logs_error(self, mock_generate):
        mock_generate.return_value = {
            "success": False,
            "message": "PDF failed",
            "path": None,
        }
        results = PDFService.generate_bulk_pdfs([self.cert])
        self.assertEqual(results["failed"], 1)
        self.assertEqual(len(results["errors"]), 1)
        self.assertEqual(results["errors"][0]["error"], "PDF failed")

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    @patch("services.pdf_service.ImageReader")
    def test_generate_pdf_template_bg_image_load_exception_uses_default(self, mock_reader, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        mock_reader.side_effect = Exception("image load error")
        template = MagicMock()
        template.background_image = MagicMock()
        template.background_image.path = "/fake/bg.png"
        template.layout_config = {}
        result = PDFService.generate_certificate_pdf(self.cert, template=template)
        self.assertTrue(result["success"])

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_draw_text_centered_when_large_x(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        template = MagicMock()
        template.background_image = None
        template.layout_config = {"participant_name": {"x": 8, "y": 3, "font_size": 28}}
        result = PDFService.generate_certificate_pdf(self.cert, template=template)
        self.assertTrue(result["success"])
        mock_c.drawCentredString.assert_called()

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_result_contains_filename_key(self, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        result = PDFService.generate_certificate_pdf(self.cert)
        self.assertIn("filename", result)
        self.assertTrue(result["filename"].endswith(".pdf"))


# ─────────────────────────────────────────────
# PASO 5 — PDF text overflow protection
# ─────────────────────────────────────────────


@pytest.mark.integration
class PDFTextOverflowTest(TestCase):
    @patch("reportlab.pdfgen.canvas.Canvas")
    @patch("services.pdf_service.PDFService.PDF_PATH")
    def test_long_name_does_not_crash_generate(self, mock_path, mock_canvas):
        mock_path.mkdir = MagicMock()
        mock_canvas.return_value = MagicMock()

        admin = User.objects.create_user(
            email="overflow_admin@test.com",
            full_name="Admin",
            password="pass",
            role="admin",
            is_staff=True,
        )
        event = Event.objects.create(
            name="Event " + "X" * 190,
            event_date=date(2026, 8, 1),
            created_by=admin,
        )
        participant = Participant.objects.create(
            document_id="OVF001",
            first_name="A" * 99,
            last_name="B" * 99,
            email="overflow@test.com",
            created_by=admin,
        )
        cert = Certificate.objects.create(
            participant=participant,
            event=event,
            generated_by=admin,
        )
        result = PDFService.generate_certificate_pdf(cert)
        self.assertTrue(result["success"])


# ─────────────────────────────────────────────
# PASO 7 — QR code generation
# ─────────────────────────────────────────────


@pytest.mark.integration
class QRCodeGenerationTest(TestCase):
    """TC-039 — QR codes are generated correctly and embedded in PDFs."""

    def setUp(self):
        self.cert, self.user = make_cert()

    def test_generate_qr_image_returns_bytesio(self):
        buf, url = PDFService._generate_qr_image("ABC123")
        self.assertIsInstance(buf, io.BytesIO)
        self.assertGreater(len(buf.read()), 0)

    def test_qr_url_contains_verification_code(self):
        code = "TESTCODE999"
        _, url = PDFService._generate_qr_image(code)
        self.assertIn(code, url)

    def test_qr_url_contains_verify_endpoint(self):
        _, url = PDFService._generate_qr_image("ABC")
        self.assertIn("/api/certificates/verify/", url)

    def test_qr_url_uses_configured_base_url(self):
        from django.test import override_settings

        with override_settings(CERTIFICATE_VERIFY_BASE_URL="https://certypro.com"):
            _, url = PDFService._generate_qr_image("XYZ")
        self.assertTrue(url.startswith("https://certypro.com"))

    def test_qr_image_is_valid_png(self):
        buf, _ = PDFService._generate_qr_image("ANYCODE")
        header = buf.read(8)
        self.assertEqual(header[:4], b"\x89PNG")

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_calls_draw_image_for_qr(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        result = PDFService.generate_certificate_pdf(self.cert)
        self.assertTrue(result["success"])
        # drawImage should be called at least once (for the QR code)
        self.assertTrue(mock_c.drawImage.called)

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    @patch("services.pdf_service.PDFService._generate_qr_image")
    def test_qr_exception_does_not_abort_pdf(self, mock_qr, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        mock_qr.side_effect = Exception("QR library unavailable")
        result = PDFService.generate_certificate_pdf(self.cert)
        self.assertTrue(result["success"])

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_draw_qr_code_positions_bottom_right(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        PDFService.generate_certificate_pdf(self.cert)
        # QR drawImage call: x should be near right edge (> halfway)
        for call in mock_c.drawImage.call_args_list:
            args, kwargs = call
            x = args[1] if len(args) > 1 else kwargs.get("x", 0)
            if x > PDFService.BASE_WIDTH / 2:
                break  # found a right-side drawImage — QR is there
        else:
            self.fail("No drawImage call found in right half of certificate (QR missing)")


# ─────────────────────────────────────────────
# PASO 7 — Instructor signature
# ─────────────────────────────────────────────


@pytest.mark.integration
class InstructorSignatureTest(TestCase):
    """TC-040 — Instructor signature is drawn on the certificate PDF."""

    def setUp(self):
        self.cert, self.user = make_cert(with_instructor=True)
        self.instructor = self.cert.event.instructor

    # --- _draw_instructor_signature unit tests ---

    def test_no_instructor_returns_silently(self):
        mock_c = MagicMock()
        PDFService._draw_instructor_signature(mock_c, None)
        mock_c.line.assert_not_called()

    def test_instructor_without_image_draws_line_and_name(self):
        mock_c = MagicMock()
        PDFService._draw_instructor_signature(mock_c, self.instructor)
        mock_c.line.assert_called_once()
        # drawCentredString called at least for the name
        self.assertTrue(mock_c.drawCentredString.called)

    def test_instructor_with_specialty_draws_specialty_text(self):
        mock_c = MagicMock()
        PDFService._draw_instructor_signature(mock_c, self.instructor)
        drawn_texts = [call.args[2] for call in mock_c.drawCentredString.call_args_list]
        self.assertTrue(
            any("Ingeniería" in t or "Software" in t for t in drawn_texts),
            msg=f"Specialty not drawn. Texts drawn: {drawn_texts}",
        )

    def test_instructor_name_drawn_on_certificate(self):
        mock_c = MagicMock()
        PDFService._draw_instructor_signature(mock_c, self.instructor)
        drawn_texts = [call.args[2] for call in mock_c.drawCentredString.call_args_list]
        self.assertTrue(
            any("Torres" in t or "Ana" in t for t in drawn_texts),
            msg=f"Instructor name not drawn. Texts: {drawn_texts}",
        )

    @patch("services.pdf_service.ImageReader")
    def test_signature_image_drawn_when_available(self, mock_reader):
        mock_c = MagicMock()
        mock_reader.return_value = MagicMock()
        # Simulate instructor with signature_image
        self.instructor.signature_image = MagicMock()
        self.instructor.signature_image.path = "/fake/sig.png"
        PDFService._draw_instructor_signature(mock_c, self.instructor)
        mock_c.drawImage.assert_called_once()

    @patch("services.pdf_service.ImageReader")
    def test_bad_signature_image_continues_gracefully(self, mock_reader):
        mock_c = MagicMock()
        mock_reader.side_effect = Exception("corrupt image")
        self.instructor.signature_image = MagicMock()
        self.instructor.signature_image.path = "/fake/bad.png"
        # Should not raise; still draws line + name
        PDFService._draw_instructor_signature(mock_c, self.instructor)
        mock_c.line.assert_called_once()

    def test_instructor_without_specialty_no_extra_text(self):
        mock_c = MagicMock()
        self.instructor.specialty = ""
        PDFService._draw_instructor_signature(mock_c, self.instructor)
        # Only one drawCentredString call (the name), not two
        self.assertEqual(mock_c.drawCentredString.call_count, 1)

    # --- Integration: full generate_certificate_pdf with instructor ---

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_with_instructor_succeeds(self, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        result = PDFService.generate_certificate_pdf(self.cert)
        self.assertTrue(result["success"])

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_without_instructor_succeeds(self, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        cert_no_instr, _ = make_cert(
            user=User.objects.create_user(email="noinstr@test.com", full_name="NoInstr", password="p"),
            doc_id="99999",
            p_email="noinstr_p@test.com",
        )
        result = PDFService.generate_certificate_pdf(cert_no_instr)
        self.assertTrue(result["success"])

    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_signature_area_uses_center(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        PDFService.generate_certificate_pdf(self.cert)
        # The signature line should be drawn near horizontal center
        for call in mock_c.line.call_args_list:
            args = call.args
            # line(x1, y1, x2, y2): x1 < center < x2
            if len(args) == 4:
                x1, y1, x2, y2 = args
                mid = (x1 + x2) / 2
                self.assertAlmostEqual(mid, PDFService.BASE_WIDTH / 2, delta=5)
                break
        else:
            self.fail("Signature line not drawn")


# ─────────────────────────────────────────────
# PASO 7 — Instructor model: signature_image field
# ─────────────────────────────────────────────


@pytest.mark.integration
class InstructorSignatureFieldTest(TestCase):
    """TC-041 — Instructor.signature_image field is correctly defined."""

    def setUp(self):
        self.user = make_admin("sig_admin@test.com")

    def test_instructor_has_signature_image_field(self):
        inst = Instructor.objects.create(full_name="Prof. Ramirez", email="ramirez@test.com", created_by=self.user)
        self.assertTrue(hasattr(inst, "signature_image"))

    def test_signature_image_defaults_to_none(self):
        inst = Instructor.objects.create(full_name="Prof. Soto", email="soto@test.com", created_by=self.user)
        self.assertFalse(bool(inst.signature_image))

    def test_signature_url_field_still_exists(self):
        inst = Instructor.objects.create(
            full_name="Prof. Vargas",
            email="vargas@test.com",
            signature_url="https://example.com/sig.png",
            created_by=self.user,
        )
        self.assertEqual(inst.signature_url, "https://example.com/sig.png")

    def test_instructor_str_unchanged(self):
        inst = Instructor.objects.create(
            full_name="Dr. Perez",
            specialty="Data Science",
            email="perez@test.com",
            created_by=self.user,
        )
        self.assertIn("Perez", str(inst))


# ─────────────────────────────────────────────
# Email limit coverage
# ─────────────────────────────────────────────


@pytest.mark.integration
class EmailLimitTest(TestCase):
    def test_send_certificate_returns_failure_when_no_recipient(self):
        cert, _ = make_cert(doc_id="LMT01", p_email="lmt01@test.com")
        result = EmailService.send_certificate(cert, "")
        self.assertFalse(result["success"])


# ─────────────────────────────────────────────
# Celery tasks exception coverage
# ─────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.integration
class PDFServiceIntegrationTest(TestCase):
    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_generate_pdf_uses_custom_signature_when_no_instructor(self, mock_mkdir, mock_canvas):
        mock_canvas.return_value = MagicMock()
        cert, user = make_cert(doc_id="CS01", p_email="cs01@test.com")
        template = MagicMock()
        template.background_image = None
        template.background_url = ""
        template.layout_config = {"signature": {"instructor_name": "Ad-Hoc Instructor", "instructor_specialty": "QA"}}
        with patch.object(PDFService, "_draw_custom_signature") as mock_custom:
            result = PDFService.generate_certificate_pdf(cert, template=template)
        self.assertTrue(result["success"])
        mock_custom.assert_called_once()

    @patch("services.pdf_service.ImageReader")
    @patch("services.pdf_service.canvas.Canvas")
    @patch("pathlib.Path.mkdir")
    def test_background_image_loads_successfully(self, mock_mkdir, mock_canvas, mock_reader):
        mock_canvas.return_value = MagicMock()
        mock_reader.return_value = MagicMock()
        cert, user = make_cert(doc_id="BG01", p_email="bg01@test.com")
        template = MagicMock()
        template.background_image = MagicMock()
        template.background_image.path = "/fake/bg.png"
        template.background_url = ""
        template.layout_config = {}
        result = PDFService.generate_certificate_pdf(cert, template=template)
        self.assertTrue(result["success"])


@pytest.mark.integration
class CeleryTasksExceptionTest(TestCase):
    """Cover exception/retry paths in services/tasks.py."""

    def test_email_task_retries_on_certificate_not_found(self):
        from services.tasks import send_certificate_email_task

        with self.assertRaises(Exception):
            result = send_certificate_email_task.apply(args=[99999, "test@test.com"])
            result.get()

    def test_pdf_task_retries_on_certificate_not_found(self):
        from services.tasks import generate_certificate_pdf_task

        with self.assertRaises(Exception):
            result = generate_certificate_pdf_task.apply(args=[99999])
            result.get()

    @patch(
        "services.email_service.EmailService.send_certificate", return_value={"success": False, "message": "API error"}
    )
    def test_email_task_retries_on_send_failure(self, mock_send):
        from services.tasks import send_certificate_email_task

        cert, _ = make_cert(doc_id="TASK01", p_email="task01@test.com")
        with self.assertRaises(Exception):
            result = send_certificate_email_task.apply(args=[cert.id, "task01@test.com"])
            result.get()

    @patch(
        "services.email_service.EmailService.send_bulk_certificates",
        return_value={"sent": 0, "failed": 0, "errors": []},
    )
    def test_bulk_certificates_task_email_method(self, mock_bulk):
        from services.tasks import send_bulk_certificates_task

        cert, _ = make_cert(doc_id="BULK01", p_email="bulk01@test.com")
        result = send_bulk_certificates_task.apply(args=[cert.event.id, "email"])
        data = result.get()
        self.assertEqual(data["sent"], 0)

    def test_bulk_certificates_task_unsupported_method(self):
        from services.tasks import send_bulk_certificates_task

        cert, _ = make_cert(doc_id="BULK02", p_email="bulk02@test.com")
        result = send_bulk_certificates_task.apply(args=[cert.event.id, "whatsapp"])
        data = result.get()
        self.assertEqual(data["sent"], 0)
        self.assertGreater(len(data["errors"]), 0)

    @patch(
        "services.pdf_service.PDFService.generate_certificate_pdf",
        return_value={"success": True, "path": "/m/cert.pdf"},
    )
    def test_pdf_task_success_path(self, mock_gen):
        from services.tasks import generate_certificate_pdf_task

        cert, _ = make_cert(doc_id="PDFTASK01", p_email="pdftask01@test.com")
        result = generate_certificate_pdf_task.apply(args=[cert.id])
        data = result.get()
        self.assertTrue(data["success"])

    @patch("services.email_service.EmailService.send_certificate", return_value={"success": True, "message": "sent"})
    def test_email_task_success_path(self, mock_send):
        from services.tasks import send_certificate_email_task

        cert, _ = make_cert(doc_id="EMLTASK01", p_email="emltask01@test.com")
        result = send_certificate_email_task.apply(args=[cert.id, "emltask01@test.com"])
        data = result.get()
        self.assertTrue(data["success"])
