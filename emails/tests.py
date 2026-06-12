from django.apps import apps
from django.test import TestCase


class EmailsAppConfigTest(TestCase):
    def test_app_config(self):
        self.assertEqual(apps.get_app_config("emails").name, "emails")
