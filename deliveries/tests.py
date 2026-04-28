from django.test import TestCase
from datetime import date
from deliveries.models import DeliveryLog
from certificados.models import Certificate, Template
from events.models import Event
from participants.models import Participant
from users.models import User


class DeliveryLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@test.com', full_name='Admin', password='pass')
        self.participant = Participant.objects.create(
            document_id='11111', first_name='Luis', last_name='Gomez',
            email='luis@test.com', created_by=self.user
        )
        self.event = Event.objects.create(name='Evento', event_date=date(2026, 1, 1), created_by=self.user)
        self.template = Template.objects.create(name='Plantilla Base', created_by=self.user)
        self.certificate = Certificate.objects.create(
            participant=self.participant, event=self.event, template=self.template, generated_by=self.user,
        )

    def _make_log(self, method='email', status='success'):
        return DeliveryLog.objects.create(
            certificate=self.certificate, sent_by=self.user,
            delivery_method=method, recipient='luis@test.com', status=status,
        )

    def test_is_successful_true(self):
        self.assertTrue(self._make_log(status='success').is_successful)

    def test_is_successful_false(self):
        self.assertFalse(self._make_log(status='error').is_successful)

    def test_is_failed_true(self):
        self.assertTrue(self._make_log(status='error').is_failed)

    def test_is_pending_true(self):
        self.assertTrue(self._make_log(status='pending').is_pending)

    def test_delivery_icon_email(self):
        self.assertEqual(self._make_log(method='email').get_delivery_icon(), '✉️')

    def test_delivery_icon_whatsapp(self):
        self.assertEqual(self._make_log(method='whatsapp').get_delivery_icon(), '💬')

    def test_delivery_icon_link(self):
        self.assertEqual(self._make_log(method='link').get_delivery_icon(), '🔗')

    def test_status_icon_success(self):
        self.assertEqual(self._make_log(status='success').get_status_icon(), '✅')

    def test_status_icon_error(self):
        self.assertEqual(self._make_log(status='error').get_status_icon(), '❌')

    def test_status_icon_pending(self):
        self.assertEqual(self._make_log(status='pending').get_status_icon(), '⏳')

    def test_str_includes_student_name_method_status(self):
        s = str(self._make_log(method='email', status='success'))
        self.assertIn('Luis', s)
        self.assertIn('email', s)
        self.assertIn('success', s)
