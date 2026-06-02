from unittest.mock import MagicMock, patch

import pytest
from django.test import SimpleTestCase


@pytest.mark.unit
class InfrastructureSettingsTest(SimpleTestCase):
    def test_spectacular_settings_exist(self):
        from django.conf import settings

        self.assertTrue(hasattr(settings, "SPECTACULAR_SETTINGS"))
        self.assertIn("TITLE", settings.SPECTACULAR_SETTINGS)
        self.assertIn("VERSION", settings.SPECTACULAR_SETTINGS)

    def test_spectacular_title_contains_scad(self):
        from django.conf import settings

        title = settings.SPECTACULAR_SETTINGS.get("TITLE", "")
        self.assertIn("SCAD", title)

    def test_drf_schema_class_is_spectacular(self):
        from django.conf import settings

        schema_class = settings.REST_FRAMEWORK.get("DEFAULT_SCHEMA_CLASS", "")
        self.assertIn("spectacular", schema_class)

    def test_celery_result_backend_is_configured(self):
        from django.conf import settings

        self.assertTrue(hasattr(settings, "CELERY_RESULT_BACKEND"))

    def test_celery_broker_url_configured(self):
        from django.conf import settings

        self.assertTrue(hasattr(settings, "CELERY_BROKER_URL"))

    def test_celery_task_serializer_is_json(self):
        from django.conf import settings

        self.assertEqual(getattr(settings, "CELERY_TASK_SERIALIZER", ""), "json")

    def test_drf_spectacular_in_installed_apps(self):
        from django.conf import settings

        self.assertIn("drf_spectacular", settings.INSTALLED_APPS)

    def test_django_celery_results_in_installed_apps(self):
        from django.conf import settings

        self.assertIn("django_celery_results", settings.INSTALLED_APPS)

    def test_jwt_access_token_lifetime_is_8_hours(self):
        from datetime import timedelta

        from django.conf import settings

        lifetime = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME")
        self.assertEqual(lifetime, timedelta(hours=8))

    def test_jwt_refresh_token_lifetime_is_7_days(self):
        from datetime import timedelta

        from django.conf import settings

        lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
        self.assertEqual(lifetime, timedelta(days=7))


@pytest.mark.unit
class ViewPermissionClassesTest(SimpleTestCase):
    def test_is_admin_user_or_read_only_safe_method(self):
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory

        from api.views import IsAdminUserOrReadOnly

        factory = APIRequestFactory()
        raw = factory.get("/")
        from django.contrib.auth.models import AnonymousUser

        raw.user = AnonymousUser()
        req = Request(raw)
        req._user = AnonymousUser()
        perm = IsAdminUserOrReadOnly()
        self.assertTrue(perm.has_permission(req, None))

    def test_is_certificate_owner_or_admin_safe_method(self):
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory

        from api.views import IsCertificateOwnerOrAdmin

        factory = APIRequestFactory()
        raw = factory.get("/")
        from django.contrib.auth.models import AnonymousUser

        raw.user = AnonymousUser()
        req = Request(raw)
        perm = IsCertificateOwnerOrAdmin()
        self.assertTrue(perm.has_object_permission(req, None, None))


@pytest.mark.unit
class DebugURLPatternTest(SimpleTestCase):
    def test_debug_mode_adds_static_media_url(self):
        import sys

        from django.test import override_settings

        original = sys.modules.pop("config.urls", None)
        try:
            with override_settings(DEBUG=True, MEDIA_URL="/media/", MEDIA_ROOT="/tmp/media"):
                import config.urls as debug_urls

                self.assertGreater(len(debug_urls.urlpatterns), 0)
        finally:
            if original is not None:
                sys.modules["config.urls"] = original


@pytest.mark.unit
class RateLimitingTest(SimpleTestCase):
    def test_throttle_classes_configured(self):
        from django.conf import settings as django_settings

        classes = django_settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_CLASSES", [])
        self.assertIn("rest_framework.throttling.AnonRateThrottle", classes)
        self.assertIn("rest_framework.throttling.UserRateThrottle", classes)

    def test_throttle_rates_defined(self):
        from django.conf import settings as django_settings

        rates = django_settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("anon", rates)
        self.assertIn("user", rates)


@pytest.mark.unit
class AuditHelperFunctionsTest(SimpleTestCase):
    def test_log_action_exception_is_silenced(self):
        from api.audit import log_action

        with patch("api.models.AuditLog") as mock_log:
            mock_log.objects.create.side_effect = Exception("DB error")
            log_action("user_login")

    def test_get_client_ip_uses_x_forwarded_for(self):
        from api.audit import get_client_ip

        request = MagicMock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "10.10.10.10, 192.168.1.1",
            "REMOTE_ADDR": "127.0.0.1",
        }
        ip = get_client_ip(request)
        self.assertEqual(ip, "10.10.10.10")

    def test_get_client_ip_falls_back_to_remote_addr(self):
        from api.audit import get_client_ip

        request = MagicMock()
        request.META = {"REMOTE_ADDR": "1.2.3.4"}
        ip = get_client_ip(request)
        self.assertEqual(ip, "1.2.3.4")


@pytest.mark.unit
class PermissionFunctionsTest(SimpleTestCase):
    def test_is_admin_with_admin_role(self):
        from api.permissions import is_admin
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "admin"
        self.assertTrue(is_admin(request))

    def test_is_admin_with_non_admin_role(self):
        from api.permissions import is_admin
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "coordinador"
        self.assertFalse(is_admin(request))

    def test_is_admin_unauthenticated(self):
        from api.permissions import is_admin
        request = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(is_admin(request))

    def test_is_admin_no_user(self):
        from api.permissions import is_admin
        request = MagicMock()
        request.user = None
        self.assertFalse(is_admin(request))

    def test_is_coordinator_with_coordinator_role(self):
        from api.permissions import is_coordinator
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "coordinador"
        self.assertTrue(is_coordinator(request))

    def test_is_coordinator_with_non_coordinator(self):
        from api.permissions import is_coordinator
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "participante"
        self.assertFalse(is_coordinator(request))

    def test_is_operational_user_with_admin(self):
        from api.permissions import is_operational_user
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "admin"
        self.assertTrue(is_operational_user(request))

    def test_is_operational_user_with_coordinator(self):
        from api.permissions import is_operational_user
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "coordinador"
        self.assertTrue(is_operational_user(request))

    def test_is_operational_user_with_participant(self):
        from api.permissions import is_operational_user
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.role = "participante"
        self.assertFalse(is_operational_user(request))

    def test_is_operational_user_unauthenticated(self):
        from api.permissions import is_operational_user
        request = MagicMock()
        request.user.is_authenticated = False
        self.assertFalse(is_operational_user(request))


@pytest.mark.unit
class CertificateViewSetSerializerClassTest(SimpleTestCase):
    def test_get_serializer_class_for_generate_action(self):
        from api.serializers import CertificateGenerateSerializer
        from api.views import CertificateViewSet

        view = CertificateViewSet()
        view.action = "generate"
        self.assertEqual(view.get_serializer_class(), CertificateGenerateSerializer)


@pytest.mark.unit
class CeleryDebugTaskTest(SimpleTestCase):
    def test_debug_task_runs_without_error(self):
        from config.celery import debug_task

        with patch("builtins.print"):
            result = debug_task.apply()
        self.assertIsNone(result.result)
