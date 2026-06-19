from datetime import date
from io import BytesIO
from unittest.mock import patch

import pandas as pd
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from certificados.models import Certificate, Template
from events.models import Enrollment, Event
from participants.models import Participant
from procesos.services import BulkCertificateGeneratorService, ExcelProcessingResult, ExcelProcessingService
from users.models import User


def make_admin():
    return User.objects.create_user(email="admin@test.com", full_name="Admin", password="pass", is_staff=True)


def make_excel(rows):
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf


@pytest.mark.integration
class ExcelProcessingServiceTest(TestCase):
    def setUp(self):
        self.user = make_admin()
        self.event = Event.objects.create(name="Taller Excel", event_date=date(2026, 5, 1), created_by=self.user)

    def _make_valid_excel(self):
        return make_excel(
            [
                {
                    "full_name": "Maria Garcia",
                    "email": "maria@test.com",
                    "document_id": "DOC001",
                    "event_name": "Taller Excel",
                    "phone": "999111222",
                }
            ]
        )

    def test_validate_file_valid_excel(self):
        buf = self._make_valid_excel()
        valid, _ = ExcelProcessingService.validate_file(buf)
        self.assertTrue(valid)

    def test_validate_file_invalid_format(self):
        buf = BytesIO(b"not an excel file")
        valid, _ = ExcelProcessingService.validate_file(buf)
        self.assertFalse(valid)

    def test_process_valid_row_creates_student(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreaterEqual(result.successful, 0)

    def test_process_missing_required_columns_raises(self):
        from procesos.services import ExcelImportError

        buf = make_excel([{"nombre": "Juan", "correo": "j@j.com"}])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with self.assertRaises(ExcelImportError):
            svc.process()

    def test_process_invalid_email(self):
        buf = make_excel(
            [
                {
                    "full_name": "Pedro",
                    "email": "not-an-email",
                    "document_id": "DOC999",
                    "event_name": "Taller Excel",
                }
            ]
        )
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertIsInstance(result, ExcelProcessingResult)

    def test_process_nonexistent_event(self):
        buf = make_excel(
            [
                {
                    "full_name": "Ana Torres",
                    "email": "ana@test.com",
                    "document_id": "DOC002",
                    "event_name": "Evento Inexistente",
                }
            ]
        )
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_bulk_generate_from_excel_returns_result(self):
        buf = self._make_valid_excel()
        result = BulkCertificateGeneratorService.generate_from_excel(buf, self.user)
        self.assertIsInstance(result, ExcelProcessingResult)


@pytest.mark.integration
class BulkCertificateGeneratorServiceTest(TestCase):
    def setUp(self):
        self.user = make_admin()
        self.participant = Participant.objects.create(
            document_id="99999",
            first_name="Luis",
            last_name="Vega",
            email="luis@test.com",
            created_by=self.user,
        )
        self.event = Event.objects.create(name="Bulk Event", event_date=date(2026, 4, 1), created_by=self.user)
        self.template = Template.objects.create(name="T", created_by=self.user)
        Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=True,
            created_by=self.user,
        )

    @patch("services.pdf_service.PDFService.generate_certificate_pdf")
    def test_generate_from_excel_creates_certificate(self, mock_pdf):
        mock_pdf.return_value = {"success": True, "path": "/media/cert.pdf"}
        cert = Certificate.objects.create(
            participant=self.participant,
            event=self.event,
            template=self.template,
            generated_by=self.user,
        )
        self.assertEqual(cert.status, "pending")
        self.assertIsNotNone(cert.verification_code)


# ─────────────────────────────────────────────
# ExcelProcessingService - exception paths & _process_rows
# ─────────────────────────────────────────────


@pytest.mark.integration
class ExcelProcessingServiceExceptionTest(TestCase):
    def setUp(self):
        self.user = make_admin()
        self.event = Event.objects.create(name="Taller Excel", event_date=date(2026, 5, 1), created_by=self.user)

    def _make_valid_excel(self):
        return make_excel(
            [
                {
                    "full_name": "Maria Garcia",
                    "email": "maria@test.com",
                    "document_id": "DOC001",
                    "event_name": "Taller Excel",
                }
            ]
        )

    def test_read_and_validate_structure_generic_exception_raises_import_error(self):
        from procesos.services import ExcelImportError

        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with patch.object(svc, "_validate_columns", side_effect=RuntimeError("unexpected")):
            with self.assertRaises(ExcelImportError):
                svc.read_and_validate_structure()

    def test_process_records_none_raises_import_error(self):
        from procesos.services import ExcelImportError

        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with self.assertRaises((ExcelImportError, TypeError)):
            svc.process_records(None)

    def test_process_generic_exception_raises_import_error(self):
        from procesos.services import ExcelImportError

        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with patch.object(svc, "read_and_validate_structure", side_effect=RuntimeError("boom")):
            with self.assertRaises(ExcelImportError):
                svc.process()

    def test_read_excel_file_empty_dataframe_raises(self):
        from procesos.services import ExcelImportError

        empty_buf = BytesIO()
        pd.DataFrame(columns=["full_name", "email", "document_id", "event_name"]).to_excel(empty_buf, index=False)
        empty_buf.seek(0)
        svc = ExcelProcessingService(empty_buf, created_by_user=self.user)
        with self.assertRaises(ExcelImportError):
            svc._read_excel_file()

    def test_read_excel_file_generic_exception_raises(self):
        from procesos.services import ExcelImportError

        svc = ExcelProcessingService(BytesIO(b"not-valid-excel"), created_by_user=self.user)
        with self.assertRaises(ExcelImportError):
            svc._read_excel_file()

    def test_process_rows_catches_row_exception(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        svc._read_excel_file()
        svc.dataframe = pd.DataFrame(
            [
                {
                    "full_name": "",
                    "email": "valid@test.com",
                    "document_id": "DOCX",
                    "event_name": "Taller Excel",
                }
            ]
        )
        svc._process_rows()
        self.assertGreater(svc.result.failed, 0)

    def test_process_row_empty_full_name_adds_error(self):
        buf = make_excel(
            [
                {
                    "full_name": "",
                    "email": "ok@test.com",
                    "document_id": "EMPTY01",
                    "event_name": "Taller Excel",
                }
            ]
        )
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_process_row_empty_email_adds_error(self):
        buf = make_excel(
            [
                {
                    "full_name": "No Email",
                    "email": "",
                    "document_id": "EMPTY02",
                    "event_name": "Taller Excel",
                }
            ]
        )
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_process_row_empty_document_id_adds_error(self):
        buf = make_excel(
            [
                {
                    "full_name": "No Doc",
                    "email": "nodoc@test.com",
                    "document_id": "",
                    "event_name": "Taller Excel",
                }
            ]
        )
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_process_row_updates_student_email_when_changed(self):
        Participant.objects.create(
            document_id="UPDATE01",
            first_name="John",
            last_name="Doe",
            email="old@test.com",
            created_by=self.user,
        )
        buf = make_excel(
            [
                {
                    "full_name": "John Doe",
                    "email": "new@test.com",
                    "document_id": "UPDATE01",
                    "event_name": "Taller Excel",
                }
            ]
        )
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with patch("services.email_service.EmailService.send_certificate", return_value={"success": True, "message": "sent"}):
            svc.process()
        participant = Participant.objects.get(document_id="UPDATE01")
        self.assertEqual(participant.email, "new@test.com")

    def test_read_excel_empty_data_error_raises_import_error(self):
        from procesos.services import ExcelImportError

        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with patch("procesos.services.pd.read_excel", side_effect=pd.errors.EmptyDataError()):
            with self.assertRaises(ExcelImportError):
                svc._read_excel_file()

    def test_process_row_empty_email_via_series(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        row = pd.Series(
            {
                "full_name": "Test",
                "email": "",
                "document_id": "D1",
                "event_name": "Taller Excel",
            }
        )
        with self.assertRaises(ValueError):
            svc._process_row(row, 0)

    def test_process_row_empty_document_id_via_series(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        row = pd.Series(
            {
                "full_name": "Test",
                "email": "x@test.com",
                "document_id": "",
                "event_name": "Taller Excel",
            }
        )
        with self.assertRaises(ValueError):
            svc._process_row(row, 0)

    def test_process_row_empty_event_name_via_series(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        row = pd.Series(
            {
                "full_name": "Test",
                "email": "y@test.com",
                "document_id": "D2",
                "event_name": "",
            }
        )
        with self.assertRaises(ValueError):
            svc._process_row(row, 0)

    def test_get_event_nonexistent_raises_value_error(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with self.assertRaises(ValueError):
            svc._get_event("Evento Que No Existe Nunca")

    def test_create_certificate_already_exists_logs_info(self):
        cert = Certificate.objects.create(
            participant=Participant.objects.create(
                document_id="CERTDUP",
                first_name="A",
                last_name="B",
                email="dup@certtest.com",
                created_by=self.user,
            ),
            event=self.event,
            generated_by=self.user,
        )
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc._create_certificate(cert.participant, self.event)
        self.assertEqual(result.id, cert.id)

    def test_validate_file_empty_excel_returns_false(self):
        buf = BytesIO()
        pd.DataFrame(columns=["full_name", "email", "document_id", "event_name"]).to_excel(buf, index=False)
        buf.seek(0)
        valid, msg = ExcelProcessingService.validate_file(buf)
        self.assertFalse(valid)
        self.assertIn("vacío", msg)

    def test_validate_file_missing_columns_returns_false(self):
        buf = make_excel([{"wrong_col": "data", "other": "value"}])
        valid, msg = ExcelProcessingService.validate_file(buf)
        self.assertFalse(valid)
        self.assertIn("faltantes", msg.lower())


@pytest.mark.integration
class ExcelProcessingServiceCoverageTest(TestCase):
    """Cover specific uncovered lines in procesos/services.py."""

    def setUp(self):
        self.user = make_admin()
        self.event = Event.objects.create(name="Proc Coverage Event", event_date=date(2026, 6, 1), created_by=self.user)
        self.participant = Participant.objects.create(
            document_id="PROC01",
            first_name="Cover",
            last_name="Test",
            email="cover@test.com",
            created_by=self.user,
        )

    def test_get_event_returns_self_event_when_set(self):
        """Line 420: return self.event when self.event is set."""
        svc = ExcelProcessingService(BytesIO(), created_by_user=self.user, event=self.event)
        result = svc._get_event(None)
        self.assertEqual(result.id, self.event.id)

    def test_get_event_raises_when_no_event_and_no_name(self):
        """Line 422: raise ValueError when self.event=None and event_name=None."""
        svc = ExcelProcessingService(BytesIO(), created_by_user=self.user)
        with self.assertRaises(ValueError):
            svc._get_event(None)

    def test_get_or_create_participant_found_by_email(self):
        """Lines 398-399: participant found by email when document_id differs."""
        svc = ExcelProcessingService(BytesIO(), created_by_user=self.user)
        result = svc._get_or_create_participant("Cover Test", "cover@test.com", "DIFFERENT_DOC")
        self.assertEqual(result.id, self.participant.id)

    def test_get_or_create_enrollment_updates_attendance(self):
        """Lines 442-443: update attendance on existing enrollment that has attendance=False."""
        from events.models import Enrollment

        enrollment = Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=False,
            created_by=self.user,
        )
        svc = ExcelProcessingService(BytesIO(), created_by_user=self.user)
        svc._get_or_create_enrollment(self.participant, self.event)
        enrollment.refresh_from_db()
        self.assertTrue(enrollment.attendance)

    def test_create_certificate_updates_template_when_bulk_has_template(self):
        """Lines 467-470: update template on existing certificate when self.template is set."""
        new_template = Template.objects.create(name="New Bulk Template", created_by=self.user)
        cert = Certificate.objects.create(
            participant=self.participant,
            event=self.event,
            generated_by=self.user,
        )
        svc = ExcelProcessingService(BytesIO(), created_by_user=self.user, template=new_template)
        result = svc._create_certificate(self.participant, self.event)
        cert.refresh_from_db()
        self.assertEqual(cert.template.id, new_template.id)
        self.assertEqual(cert.status, "pending")

    @patch(
        "services.email_service.EmailService.send_certificate", return_value={"success": False, "message": "SMTP fail"}
    )
    @patch(
        "services.pdf_service.PDFService.generate_certificate_pdf",
        return_value={"success": True, "path": "/m/cert.pdf"},
    )
    def test_delivery_failure_raises_value_error_in_process_row(self, mock_pdf, mock_email):
        """Line 359: raise ValueError when delivery fails."""
        buf = make_excel(
            [
                {
                    "full_name": "Cover Test",
                    "email": "cover@test.com",
                    "document_id": "PROC01",
                    "event_name": "Proc Coverage Event",
                }
            ]
        )
        svc = ExcelProcessingService(buf, created_by_user=self.user, event=self.event)
        result = svc.process()
        self.assertGreater(result.failed, 0)


class BulkTemplateCreationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="bulk@test.com", full_name="Bulk", password="bulkPass99!")
        self.event = Event.objects.create(name="Bulk Event", event_date=date(2026, 6, 1), created_by=self.user)

    def test_default_y_coord_when_no_name_y(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {"name_x": "50"}
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        expected_y = (1 - 40 / 100) * 595.28 / 72
        self.assertAlmostEqual(tpl.y_coord, expected_y, places=2)
        self.assertEqual(tpl.layout_config["participant_name"]["x"], tpl.x_coord)

    def test_custom_y_coord_calculation(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {"name_x": "30", "name_y": "70", "font_size": "24"}
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        expected_x = 30 / 100 * 841.89 / 72
        expected_y = (1 - 70 / 100) * 595.28 / 72
        self.assertAlmostEqual(tpl.x_coord, expected_x, places=2)
        self.assertAlmostEqual(tpl.y_coord, expected_y, places=2)
        self.assertEqual(tpl.layout_config["participant_name"]["font_size"], 24)

    def test_custom_font_family_and_color(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {"name_x": "50", "name_y": "50", "font_family": "Times-Roman", "font_color": "#FF0000"}
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        self.assertEqual(tpl.layout_config["participant_name"]["font_family"], "Times-Roman")
        self.assertEqual(tpl.layout_config["participant_name"]["color"], "#FF0000")

    def test_default_font_family_and_color(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {"name_x": "50", "name_y": "50"}
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        self.assertEqual(tpl.layout_config["participant_name"]["font_family"], "Helvetica")
        self.assertEqual(tpl.layout_config["participant_name"]["color"], "#000000")

    def test_template_is_inactive(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {"name_x": "50", "name_y": "50"}
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        self.assertFalse(tpl.is_active)

    def test_signature_with_instructor_name_and_specialty(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {
            "name_x": "50",
            "name_y": "50",
            "instructor_name": "Dr. Perez",
            "instructor_specialty": "Medicina",
        }
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        self.assertIn("signature", tpl.layout_config)
        self.assertEqual(tpl.layout_config["signature"]["instructor_name"], "Dr. Perez")
        self.assertEqual(tpl.layout_config["signature"]["instructor_specialty"], "Medicina")

    def test_signature_without_specialty_defaults_empty(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {"name_x": "50", "name_y": "50", "instructor_name": "Prof. Lopez"}
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        self.assertEqual(tpl.layout_config["signature"]["instructor_specialty"], "")

    def test_no_signature_when_instructor_name_missing(self):
        img = SimpleUploadedFile("tpl.png", b"data", content_type="image/png")
        config = {"name_x": "50", "name_y": "50"}
        tpl = ExcelProcessingService.create_bulk_template(self.event, self.user, img, config)
        self.assertNotIn("signature", tpl.layout_config)
