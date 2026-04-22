from django.test import TestCase
from instructors.models import Instructor
from users.models import User


class InstructorModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@test.com', full_name='Admin', password='pass')

    def _make_instructor(self, name='Carlos Lopez', specialty='Python', email='carlos@test.com'):
        return Instructor.objects.create(
            full_name=name, specialty=specialty, email=email, created_by=self.user,
        )

    def test_str_with_specialty(self):
        inst = self._make_instructor()
        self.assertIn('Carlos Lopez', str(inst))
        self.assertIn('Python', str(inst))

    def test_str_without_specialty(self):
        inst = Instructor.objects.create(full_name='Sin Especialidad', email='sin@test.com', created_by=self.user)
        self.assertEqual(str(inst), 'Sin Especialidad')

    def test_is_active_default_true(self):
        inst = self._make_instructor()
        self.assertTrue(inst.is_active)

    def test_email_is_unique(self):
        self._make_instructor(email='dup@test.com')
        with self.assertRaises(Exception):
            Instructor.objects.create(full_name='Otro', email='dup@test.com', created_by=self.user)

    def test_blank_fields_default_empty(self):
        inst = self._make_instructor()
        self.assertEqual(inst.phone, '')
        self.assertEqual(inst.bio, '')
        self.assertEqual(inst.signature_url, '')
