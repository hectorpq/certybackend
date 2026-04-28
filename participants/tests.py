from django.test import TestCase

from participants.models import Participant
from users.models import User


class ParticipantModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com", full_name="Admin", password="pass"
        )

    def _make_participant(
        self, doc="12345678", email="participant@test.com", first="Juan", last="Perez"
    ):
        return Participant.objects.create(
            document_id=doc,
            first_name=first,
            last_name=last,
            email=email,
            created_by=self.user,
        )

    def test_full_name_property(self):
        p = self._make_participant()
        self.assertEqual(p.full_name, "Juan Perez")

    def test_str_includes_document_id(self):
        p = self._make_participant()
        self.assertIn("12345678", str(p))

    def test_str_includes_full_name(self):
        p = self._make_participant()
        self.assertIn("Juan", str(p))
        self.assertIn("Perez", str(p))

    def test_is_active_default_true(self):
        p = self._make_participant()
        self.assertTrue(p.is_active)

    def test_document_id_is_unique(self):
        self._make_participant(doc="99999", email="a@test.com")
        with self.assertRaises(Exception):
            self._make_participant(doc="99999", email="b@test.com")

    def test_email_is_unique(self):
        self._make_participant(doc="11111", email="dup@test.com")
        with self.assertRaises(Exception):
            self._make_participant(doc="22222", email="dup@test.com")

    def test_phone_defaults_to_empty(self):
        p = self._make_participant()
        self.assertEqual(p.phone, "")
