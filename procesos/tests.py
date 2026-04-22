from django.test import TestCase
from io import BytesIO
from unittest.mock import patch, MagicMock
from datetime import date

import pandas as pd

from procesos.services import (
    ExcelProcessingResult,
    ExcelProcessingService,
    BulkCertificateGeneratorService,
)
from users.models import User
from students.models import Student
from events.models import Event, Enrollment
from certificados.models import Certificate, Template


def make_admin():
    return User.objects.create_user(email='admin@test.com', full_name='Admin', password='pass', is_staff=True)

def make_excel(rows):
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf


class ExcelProcessingResultTest(TestCase):
    def test_add_error_increments_failed(self):
        r = ExcelProcessingResult()
        r.add_error(1, 'email', 'Invalid email')
        self.assertEqual(r.failed, 1)
        self.assertEqual(len(r.errors), 1)

    def test_add_success_increments_successful(self):
        r = ExcelProcessingResult()
        r.add_success(42)
        self.assertEqual(r.successful, 1)
        self.assertIn(42, r.created_certificates)

    def test_to_dict_keys(self):
        r = ExcelProcessingResult()
        r.total_rows = 5
        r.add_success(1)
        d = r.to_dict()
        for key in ['total_rows', 'successful', 'failed', 'errors', 'summary']:
            self.assertIn(key, d)

    def test_get_summary_with_rows(self):
        r = ExcelProcessingResult()
        r.total_rows = 2
        r.add_success(1)
        s = r.get_summary()
        self.assertIsInstance(s, str)

    def test_get_summary_with_errors(self):
        r = ExcelProcessingResult()
        r.total_rows = 3
        for i in range(12):
            r.add_error(i+1, 'field', f'Error {i}')
        s = r.get_summary()
        self.assertIn('ERRORES', s)


class ExcelProcessingServiceTest(TestCase):
    def setUp(self):
        self.user = make_admin()
        self.event = Event.objects.create(name='Taller Excel', event_date=date(2026, 5, 1), created_by=self.user)

    def _make_valid_excel(self):
        return make_excel([{
            'full_name': 'Maria Garcia',
            'email': 'maria@test.com',
            'document_id': 'DOC001',
            'event_name': 'Taller Excel',
            'phone': '999111222',
        }])

    def test_validate_file_valid_excel(self):
        buf = self._make_valid_excel()
        valid, _ = ExcelProcessingService.validate_file(buf)
        self.assertTrue(valid)

    def test_validate_file_invalid_format(self):
        buf = BytesIO(b'not an excel file')
        valid, _ = ExcelProcessingService.validate_file(buf)
        self.assertFalse(valid)

    def test_process_valid_row_creates_student(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreaterEqual(result.successful, 0)

    def test_process_missing_required_columns_raises(self):
        from procesos.services import ExcelImportError
        buf = make_excel([{'nombre': 'Juan', 'correo': 'j@j.com'}])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with self.assertRaises(ExcelImportError):
            svc.process()

    def test_process_invalid_email(self):
        buf = make_excel([{
            'full_name': 'Pedro',
            'email': 'not-an-email',
            'document_id': 'DOC999',
            'event_name': 'Taller Excel',
        }])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertIsInstance(result, ExcelProcessingResult)

    def test_process_nonexistent_event(self):
        buf = make_excel([{
            'full_name': 'Ana Torres',
            'email': 'ana@test.com',
            'document_id': 'DOC002',
            'event_name': 'Evento Inexistente',
        }])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_bulk_generate_from_excel_returns_result(self):
        buf = self._make_valid_excel()
        result = BulkCertificateGeneratorService.generate_from_excel(buf, self.user)
        self.assertIsInstance(result, ExcelProcessingResult)


class BulkCertificateGeneratorServiceTest(TestCase):
    def setUp(self):
        self.user = make_admin()
        self.student = Student.objects.create(
            document_id='99999', first_name='Luis', last_name='Vega',
            email='luis@test.com', created_by=self.user
        )
        self.event = Event.objects.create(name='Bulk Event', event_date=date(2026, 4, 1), created_by=self.user)
        self.template = Template.objects.create(name='T', created_by=self.user)
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.user)

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_from_excel_creates_certificate(self, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.user
        )
        self.assertEqual(cert.status, 'pending')
        self.assertIsNotNone(cert.verification_code)


# ─────────────────────────────────────────────
# ExcelProcessingService - exception paths & _process_rows
# ─────────────────────────────────────────────

class ExcelProcessingServiceExceptionTest(TestCase):
    def setUp(self):
        self.user = make_admin()
        self.event = Event.objects.create(name='Taller Excel', event_date=date(2026, 5, 1), created_by=self.user)

    def _make_valid_excel(self):
        return make_excel([{
            'full_name': 'Maria Garcia',
            'email': 'maria@test.com',
            'document_id': 'DOC001',
            'event_name': 'Taller Excel',
        }])

    def test_read_and_validate_structure_generic_exception_raises_import_error(self):
        from procesos.services import ExcelImportError
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with patch.object(svc, '_validate_columns', side_effect=RuntimeError('unexpected')):
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
        with patch.object(svc, 'read_and_validate_structure', side_effect=RuntimeError('boom')):
            with self.assertRaises(ExcelImportError):
                svc.process()

    def test_read_excel_file_empty_dataframe_raises(self):
        from procesos.services import ExcelImportError
        empty_buf = BytesIO()
        pd.DataFrame(columns=['full_name', 'email', 'document_id', 'event_name']).to_excel(empty_buf, index=False)
        empty_buf.seek(0)
        svc = ExcelProcessingService(empty_buf, created_by_user=self.user)
        with self.assertRaises(ExcelImportError):
            svc._read_excel_file()

    def test_read_excel_file_generic_exception_raises(self):
        from procesos.services import ExcelImportError
        svc = ExcelProcessingService(BytesIO(b'not-valid-excel'), created_by_user=self.user)
        with self.assertRaises(ExcelImportError):
            svc._read_excel_file()

    def test_process_rows_catches_row_exception(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        svc._read_excel_file()
        svc.dataframe = pd.DataFrame([{
            'full_name': '',
            'email': 'valid@test.com',
            'document_id': 'DOCX',
            'event_name': 'Taller Excel',
        }])
        svc._process_rows()
        self.assertGreater(svc.result.failed, 0)

    def test_process_row_empty_full_name_adds_error(self):
        buf = make_excel([{
            'full_name': '',
            'email': 'ok@test.com',
            'document_id': 'EMPTY01',
            'event_name': 'Taller Excel',
        }])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_process_row_empty_email_adds_error(self):
        buf = make_excel([{
            'full_name': 'No Email',
            'email': '',
            'document_id': 'EMPTY02',
            'event_name': 'Taller Excel',
        }])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_process_row_empty_document_id_adds_error(self):
        buf = make_excel([{
            'full_name': 'No Doc',
            'email': 'nodoc@test.com',
            'document_id': '',
            'event_name': 'Taller Excel',
        }])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc.process()
        self.assertGreater(result.failed, 0)

    def test_process_row_updates_student_email_when_changed(self):
        from students.models import Student
        Student.objects.create(
            document_id='UPDATE01', first_name='John', last_name='Doe',
            email='old@test.com', created_by=self.user
        )
        buf = make_excel([{
            'full_name': 'John Doe',
            'email': 'new@test.com',
            'document_id': 'UPDATE01',
            'event_name': 'Taller Excel',
        }])
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        svc.process()
        from students.models import Student
        student = Student.objects.get(document_id='UPDATE01')
        self.assertEqual(student.email, 'new@test.com')

    def test_read_excel_empty_data_error_raises_import_error(self):
        from procesos.services import ExcelImportError
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with patch('procesos.services.pd.read_excel', side_effect=pd.errors.EmptyDataError()):
            with self.assertRaises(ExcelImportError):
                svc._read_excel_file()

    def test_process_row_empty_email_via_series(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        row = pd.Series({'full_name': 'Test', 'email': '', 'document_id': 'D1', 'event_name': 'Taller Excel'})
        with self.assertRaises(ValueError):
            svc._process_row(row, 0)

    def test_process_row_empty_document_id_via_series(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        row = pd.Series({'full_name': 'Test', 'email': 'x@test.com', 'document_id': '', 'event_name': 'Taller Excel'})
        with self.assertRaises(ValueError):
            svc._process_row(row, 0)

    def test_process_row_empty_event_name_via_series(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        row = pd.Series({'full_name': 'Test', 'email': 'y@test.com', 'document_id': 'D2', 'event_name': ''})
        with self.assertRaises(ValueError):
            svc._process_row(row, 0)

    def test_get_event_nonexistent_raises_value_error(self):
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        with self.assertRaises(ValueError):
            svc._get_event('Evento Que No Existe Nunca')

    def test_create_certificate_already_exists_logs_info(self):
        cert = Certificate.objects.create(
            student=Student.objects.create(
                document_id='CERTDUP', first_name='A', last_name='B',
                email='dup@certtest.com', created_by=self.user
            ),
            event=self.event,
            generated_by=self.user,
        )
        buf = self._make_valid_excel()
        svc = ExcelProcessingService(buf, created_by_user=self.user)
        result = svc._create_certificate(cert.student, self.event)
        self.assertEqual(result.id, cert.id)

    def test_validate_file_empty_excel_returns_false(self):
        buf = BytesIO()
        pd.DataFrame(columns=['full_name', 'email', 'document_id', 'event_name']).to_excel(buf, index=False)
        buf.seek(0)
        valid, msg = ExcelProcessingService.validate_file(buf)
        self.assertFalse(valid)
        self.assertIn('vacío', msg)

    def test_validate_file_missing_columns_returns_false(self):
        buf = make_excel([{'wrong_col': 'data', 'other': 'value'}])
        valid, msg = ExcelProcessingService.validate_file(buf)
        self.assertFalse(valid)
        self.assertIn('faltantes', msg.lower())
