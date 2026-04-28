from django.test import TestCase

from users.models import User


class UserManagerTest(TestCase):
    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="TEST@EXAMPLE.COM", full_name="Juan", password="pass123"
        )
        self.assertEqual(user.email, "TEST@example.com")

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", full_name="Juan", password="pass123")

    def test_create_user_default_role_is_participante(self):
        user = User.objects.create_user(
            email="juan@test.com", full_name="Juan", password="pass123"
        )
        self.assertEqual(user.role, "participante")

    def test_create_user_is_active_by_default(self):
        user = User.objects.create_user(
            email="active@test.com", full_name="Juan", password="pass123"
        )
        self.assertTrue(user.is_active)

    def test_create_superuser_has_admin_role(self):
        user = User.objects.create_superuser(
            email="admin@test.com", full_name="Admin", password="pass123"
        )
        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_user_str_includes_name_and_role(self):
        user = User.objects.create_user(
            email="str@test.com", full_name="Maria", password="pass123", role="admin"
        )
        self.assertIn("Maria", str(user))
        self.assertIn("Admin", str(user))

    def test_user_str_shows_active_check(self):
        user = User.objects.create_user(
            email="check@test.com", full_name="Pedro", password="pass123"
        )
        self.assertIn("✓", str(user))

    def test_inactive_user_str_shows_cross(self):
        user = User.objects.create_user(
            email="inactive@test.com", full_name="Pedro", password="pass123"
        )
        user.is_active = False
        user.save()
        self.assertIn("✗", str(user))

    def test_email_is_unique(self):
        User.objects.create_user(
            email="unique@test.com", full_name="A", password="pass"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="unique@test.com", full_name="B", password="pass"
            )

    def test_admin_mode_disabled_by_default(self):
        user = User.objects.create_user(
            email="mode@test.com", full_name="A", password="pass"
        )
        self.assertFalse(user.admin_mode_enabled)
