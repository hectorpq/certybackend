from django.test import TestCase
from students.models import Student
from users.models import User


class StudentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@test.com', full_name='Admin', password='pass')

    def _make_student(self, doc='12345678', email='student@test.com', first='Juan', last='Perez'):
        return Student.objects.create(
            document_id=doc, first_name=first, last_name=last,
            email=email, created_by=self.user,
        )

    def test_full_name_property(self):
        s = self._make_student()
        self.assertEqual(s.full_name, 'Juan Perez')

    def test_str_includes_document_id(self):
        s = self._make_student()
        self.assertIn('12345678', str(s))

    def test_str_includes_full_name(self):
        s = self._make_student()
        self.assertIn('Juan', str(s))
        self.assertIn('Perez', str(s))

    def test_is_active_default_true(self):
        s = self._make_student()
        self.assertTrue(s.is_active)

    def test_document_id_is_unique(self):
        self._make_student(doc='99999', email='a@test.com')
        with self.assertRaises(Exception):
            self._make_student(doc='99999', email='b@test.com')

    def test_email_is_unique(self):
        self._make_student(doc='11111', email='dup@test.com')
        with self.assertRaises(Exception):
            self._make_student(doc='22222', email='dup@test.com')

    def test_phone_defaults_to_empty(self):
        s = self._make_student()
        self.assertEqual(s.phone, '')
