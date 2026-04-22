from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
from datetime import date
from pathlib import Path

from services.email_service import EmailService
from services.pdf_service import PDFService
from users.models import User
from students.models import Student
from events.models import Event
from certificados.models import Certificate, Template


def make_admin():
    return User.objects.create_user(email='admin@test.com', full_name='Admin', password='pass')

def make_cert():
    user = make_admin()
    student = Student.objects.create(
        document_id='11111', first_name='Luis', last_name='Gomez',
        email='luis@test.com', phone='999000111', created_by=user
    )
    event = Event.objects.create(name='Workshop', event_date=date(2026, 6, 1), created_by=user)
    template = Template.objects.create(name='Base', created_by=user)
    cert = Certificate.objects.create(
        student=student, event=event, template=template, generated_by=user
    )
    return cert, user


# ─────────────────────────────────────────────
# EmailService
# ─────────────────────────────────────────────

class EmailServiceTest(TestCase):
    def setUp(self):
        self.cert, self.user = make_cert()

    def test_send_no_recipient_returns_failure(self):
        result = EmailService.send_certificate(self.cert, '')
        self.assertFalse(result['success'])
        self.assertIn('No email', result['message'])

    @patch('services.email_service.EmailMessage')
    def test_send_certificate_success(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 1
        mock_email.return_value = mock_msg
        result = EmailService.send_certificate(self.cert, 'test@test.com')
        self.assertTrue(result['success'])

    @patch('services.email_service.EmailMessage')
    def test_send_certificate_smtp_returns_zero(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 0
        mock_email.return_value = mock_msg
        result = EmailService.send_certificate(self.cert, 'test@test.com')
        self.assertFalse(result['success'])

    @patch('services.email_service.EmailMessage')
    def test_send_certificate_exception_returns_failure(self, mock_email):
        mock_email.side_effect = Exception('SMTP error')
        result = EmailService.send_certificate(self.cert, 'test@test.com')
        self.assertFalse(result['success'])
        self.assertIn('SMTP error', result['message'])

    @patch('services.email_service.EmailMessage')
    def test_send_bulk_all_success(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 1
        mock_email.return_value = mock_msg
        result = EmailService.send_bulk_certificates([self.cert])
        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 0)

    @patch('services.email_service.EmailMessage')
    def test_send_bulk_with_recipient_map(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 1
        mock_email.return_value = mock_msg
        result = EmailService.send_bulk_certificates(
            [self.cert], recipient_map={self.cert.id: 'custom@test.com'}
        )
        self.assertEqual(result['sent'], 1)

    @patch('services.email_service.EmailMessage')
    def test_send_bulk_failure_logged(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 0
        mock_email.return_value = mock_msg
        result = EmailService.send_bulk_certificates([self.cert])
        self.assertEqual(result['failed'], 1)
        self.assertEqual(len(result['errors']), 1)

    @patch('services.email_service.EmailMessage')
    def test_send_certificate_attaches_pdf_when_present(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 1
        mock_email.return_value = mock_msg
        self.cert.pdf_url = '/media/certificates/cert.pdf'
        self.cert.save()
        with patch('builtins.open', mock_open(read_data=b'%PDF')):
            with patch('pathlib.Path.exists', return_value=True):
                result = EmailService.send_certificate(self.cert, 'test@test.com')
        self.assertTrue(result['success'])

    @patch('services.email_service.EmailMessage')
    def test_send_certificate_pdf_not_on_disk_logs_warning(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 1
        mock_email.return_value = mock_msg
        self.cert.pdf_url = '/media/certificates/missing.pdf'
        self.cert.save()
        with patch('pathlib.Path.exists', return_value=False):
            result = EmailService.send_certificate(self.cert, 'test@test.com')
        self.assertTrue(result['success'])

    @patch('services.email_service.EmailMessage')
    def test_send_certificate_pdf_attach_exception_continues(self, mock_email):
        mock_msg = MagicMock()
        mock_msg.send.return_value = 1
        mock_email.return_value = mock_msg
        self.cert.pdf_url = '/media/certificates/cert.pdf'
        self.cert.save()
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=IOError('disk error')):
                result = EmailService.send_certificate(self.cert, 'test@test.com')
        self.assertTrue(result['success'])


# ─────────────────────────────────────────────
# PDFService
# ─────────────────────────────────────────────

class PDFServiceTest(TestCase):
    def setUp(self):
        self.cert, self.user = make_cert()

    @patch('services.pdf_service.canvas.Canvas')
    @patch('pathlib.Path.mkdir')
    def test_generate_pdf_success_no_template(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        result = PDFService.generate_certificate_pdf(self.cert, template=None)
        self.assertTrue(result['success'])
        self.assertIn('path', result)

    @patch('services.pdf_service.canvas.Canvas')
    @patch('pathlib.Path.mkdir')
    def test_generate_pdf_with_template_no_bg(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        template = Template.objects.create(name='T2', created_by=self.user)
        result = PDFService.generate_certificate_pdf(self.cert, template=template)
        self.assertTrue(result['success'])

    @patch('services.pdf_service.canvas.Canvas')
    @patch('pathlib.Path.mkdir')
    def test_generate_pdf_canvas_exception(self, mock_mkdir, mock_canvas):
        mock_canvas.side_effect = Exception('canvas error')
        result = PDFService.generate_certificate_pdf(self.cert)
        self.assertFalse(result['success'])
        self.assertIn('canvas error', result['message'])

    @patch('services.pdf_service.canvas.Canvas')
    @patch('pathlib.Path.mkdir')
    def test_generate_bulk_pdfs(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        results = PDFService.generate_bulk_pdfs([self.cert])
        self.assertIn('generated', results)
        self.assertIn('failed', results)

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_bulk_pdfs_failure_logs_error(self, mock_generate):
        mock_generate.return_value = {'success': False, 'message': 'PDF failed', 'path': None}
        results = PDFService.generate_bulk_pdfs([self.cert])
        self.assertEqual(results['failed'], 1)
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['error'], 'PDF failed')

    @patch('services.pdf_service.canvas.Canvas')
    @patch('pathlib.Path.mkdir')
    @patch('services.pdf_service.ImageReader')
    def test_generate_pdf_template_bg_image_load_exception_uses_default(self, mock_reader, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        mock_reader.side_effect = Exception('image load error')
        template = MagicMock()
        template.background_image = MagicMock()
        template.background_image.path = '/fake/bg.png'
        template.layout_config = {}
        result = PDFService.generate_certificate_pdf(self.cert, template=template)
        self.assertTrue(result['success'])

    @patch('services.pdf_service.canvas.Canvas')
    @patch('pathlib.Path.mkdir')
    def test_generate_pdf_draw_text_centered_when_large_x(self, mock_mkdir, mock_canvas):
        mock_c = MagicMock()
        mock_canvas.return_value = mock_c
        template = MagicMock()
        template.background_image = None
        template.layout_config = {
            'student_name': {'x': 8, 'y': 3, 'font_size': 28},
        }
        result = PDFService.generate_certificate_pdf(self.cert, template=template)
        self.assertTrue(result['success'])
        mock_c.drawCentredString.assert_called()
