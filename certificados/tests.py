import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, date
from unittest.mock import patch, MagicMock

from certificados.models import Template, Certificate
from events.models import Event, Enrollment
from students.models import Student
from users.models import User


class TemplateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@test.com', full_name='Admin', password='pass')

    def test_str_with_category(self):
        t = Template.objects.create(name='Clasico', category='Cursos', created_by=self.user)
        self.assertIn('Clasico', str(t))
        self.assertIn('Cursos', str(t))

    def test_str_without_category(self):
        t = Template.objects.create(name='Sin Cat', created_by=self.user)
        self.assertEqual(str(t), 'Sin Cat')

    def test_is_active_default_true(self):
        t = Template.objects.create(name='T1', created_by=self.user)
        self.assertTrue(t.is_active)

    def test_default_font_values(self):
        t = Template.objects.create(name='T2', created_by=self.user)
        self.assertEqual(t.font_color, '#000000')
        self.assertEqual(t.font_family, 'Helvetica')
        self.assertEqual(t.font_size, 24)


class CertificateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@test.com', full_name='Admin', password='pass')
        self.student = Student.objects.create(
            document_id='11111', first_name='Luis', last_name='Gomez',
            email='luis@test.com', phone='999000111', created_by=self.user
        )
        self.event = Event.objects.create(name='Taller Test', event_date=date(2026, 1, 1), created_by=self.user)
        self.template = Template.objects.create(name='Base', created_by=self.user)

    def _make_cert(self, status='pending'):
        cert = Certificate(
            student=self.student, event=self.event,
            template=self.template, generated_by=self.user,
            verification_code='',
        )
        cert.save()
        if status != 'pending':
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
        self.assertIn('Luis', s)
        self.assertIn('Taller Test', s)
        self.assertIn('pending', s)

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
        code = Certificate.generate_verification_code(1, 2)
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
        self.assertEqual(cert.delivery_status, 'pending')

    def test_determine_recipient_email(self):
        cert = self._make_cert()
        self.assertEqual(cert._determine_recipient('email'), 'luis@test.com')

    def test_determine_recipient_whatsapp_uses_phone(self):
        cert = self._make_cert()
        self.assertEqual(cert._determine_recipient('whatsapp'), '999000111')

    def test_determine_recipient_whatsapp_fallback_to_email(self):
        self.student.phone = ''
        self.student.save()
        cert = self._make_cert()
        self.assertEqual(cert._determine_recipient('whatsapp'), 'luis@test.com')

    def test_determine_recipient_link(self):
        cert = self._make_cert()
        self.assertEqual(cert._determine_recipient('link'), 'luis@test.com')

    def test_update_delivery_status_success(self):
        cert = self._make_cert()
        log = MagicMock()
        cert._update_delivery_status(log, {'success': True, 'message': 'ok'})
        self.assertEqual(cert.status, 'sent')
        self.assertEqual(log.status, 'success')

    def test_update_delivery_status_failure(self):
        cert = self._make_cert()
        log = MagicMock()
        cert._update_delivery_status(log, {'success': False, 'message': 'error!'})
        self.assertEqual(cert.status, 'failed')
        self.assertEqual(log.status, 'error')
        self.assertEqual(log.error_message, 'error!')

    def test_mark_as_failed_raises_when_pending(self):
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.mark_as_failed('some error')

    def test_mark_as_failed_on_generated_cert(self):
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status='generated')
        cert.refresh_from_db()
        cert.mark_as_failed('PDF error')
        cert.refresh_from_db()
        self.assertEqual(cert.status, 'failed')

    def test_generate_raises_if_not_pending(self):
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status='generated')
        cert.refresh_from_db()
        with self.assertRaises(ValidationError):
            cert.generate(skip_attendance_check=True)

    def test_generate_raises_if_student_not_enrolled(self):
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.generate()

    def test_generate_raises_if_student_absent(self):
        Enrollment.objects.create(student=self.student, event=self.event, attendance=False, created_by=self.user)
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.generate()

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_success(self, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.user)
        cert = self._make_cert()
        result = cert.generate(generated_by=self.user, template=self.template)
        self.assertEqual(result.status, 'generated')
        self.assertEqual(result.pdf_url, '/media/cert.pdf')

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_raises_on_pdf_failure(self, mock_pdf):
        mock_pdf.return_value = {'success': False, 'message': 'render error'}
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.user)
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.generate()

    @patch('services.email_service.EmailService.send_certificate')
    def test_deliver_via_email(self, mock_send):
        mock_send.return_value = {'success': True, 'message': 'sent'}
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status='generated', pdf_url='/media/c.pdf')
        cert.refresh_from_db()
        log = cert.deliver(method='email', sent_by=self.user)
        self.assertEqual(log.status, 'success')
        self.assertTrue(cert.has_delivery_attempts())

    def test_deliver_raises_if_not_generated(self):
        cert = self._make_cert()
        with self.assertRaises(ValidationError):
            cert.deliver(method='email')

    def test_send_delivery_link_always_succeeds(self):
        cert = self._make_cert()
        cert.pdf_url = '/media/cert.pdf'
        result = cert._send_delivery('link', 'luis@test.com')
        self.assertTrue(result['success'])

    def test_send_delivery_unknown_method_raises(self):
        cert = self._make_cert()
        with self.assertRaises(Exception):
            cert._send_delivery('fax', 'luis@test.com')

    @patch('services.whatsapp_service.get_whatsapp_service')
    def test_send_delivery_whatsapp_calls_service(self, mock_get):
        mock_ws = MagicMock()
        mock_ws.send_certificate.return_value = {'success': True, 'message': 'sent'}
        mock_get.return_value = mock_ws
        cert = self._make_cert()
        result = cert._send_delivery('whatsapp', '999000111')
        self.assertTrue(result['success'])

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_sets_verification_code_when_empty(self, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.user)
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(verification_code='')
        cert.refresh_from_db()
        self.assertEqual(cert.verification_code, '')
        result = cert.generate(generated_by=self.user, skip_attendance_check=True)
        self.assertNotEqual(result.verification_code, '')

    def test_deliver_raises_when_no_recipient(self):
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(status='generated')
        cert.refresh_from_db()
        with patch.object(cert, '_determine_recipient', return_value=''):
            with self.assertRaises(Exception):
                cert.deliver(method='email')
