import pytest
from django.test import TestCase


@pytest.mark.integration
class DeliveryQueryHelpersTest(TestCase):
    def setUp(self):
        from certificados.models import Certificate, Template
        from deliveries.models import DeliveryLog
        from events.models import Event
        from participants.models import Participant
        from users.models import User

        self.user = User.objects.create_user(email="h@test.com", full_name="Helper", password="pass")
        self.participant = Participant.objects.create(
            document_id="77777",
            first_name="Pia",
            last_name="Lima",
            email="pia@test.com",
            created_by=self.user,
        )
        import datetime

        self.event = Event.objects.create(name="Q Event", event_date=datetime.date(2026, 3, 1), created_by=self.user)
        self.template = Template.objects.create(name="T", created_by=self.user)
        self.cert = Certificate.objects.create(
            participant=self.participant,
            event=self.event,
            template=self.template,
            generated_by=self.user,
        )
        self.log = DeliveryLog.objects.create(
            certificate=self.cert,
            sent_by=self.user,
            delivery_method="email",
            recipient="pia@test.com",
            status="success",
        )

    def test_get_recent_deliveries_returns_queryset(self):
        from core.helpers import get_recent_deliveries

        result = get_recent_deliveries(self.cert, days=30)
        self.assertEqual(result.count(), 1)

    def test_get_successful_deliveries_returns_queryset(self):
        from core.helpers import get_successful_deliveries

        result = get_successful_deliveries(self.cert)
        self.assertEqual(result.count(), 1)

    def test_get_failed_deliveries_returns_empty(self):
        from core.helpers import get_failed_deliveries

        result = get_failed_deliveries(self.cert)
        self.assertEqual(result.count(), 0)


@pytest.mark.integration
class SoftDeleteMixinTest(TestCase):
    """Tests for SoftDeleteMixin — covering the restore() method and manager."""

    def setUp(self):
        from users.models import User

        self.user = User.objects.create_user(email="softdelete@test.com", full_name="Soft", password="pass")

    def _make_participant(self, doc="SD001", email="sd@test.com"):
        from participants.models import Participant

        return Participant.objects.create(
            document_id=doc,
            first_name="A",
            last_name="B",
            email=email,
            created_by=self.user,
        )

    def test_soft_delete_sets_is_deleted(self):
        p = self._make_participant()
        p.delete(deleted_by=self.user)
        p.refresh_from_db()
        self.assertTrue(p.is_deleted)
        self.assertIsNotNone(p.deleted_at)
        self.assertEqual(p.deleted_by, self.user)

    def test_soft_deleted_excluded_from_objects(self):
        p = self._make_participant()
        p.delete()
        from participants.models import Participant

        self.assertFalse(Participant.objects.filter(pk=p.pk).exists())

    def test_soft_deleted_visible_in_all_objects(self):
        p = self._make_participant()
        p.delete()
        from participants.models import Participant

        self.assertTrue(Participant.all_objects.filter(pk=p.pk).exists())

    def test_restore_clears_is_deleted(self):
        p = self._make_participant()
        p.delete(deleted_by=self.user)
        p.restore()
        p.refresh_from_db()
        self.assertFalse(p.is_deleted)
        self.assertIsNone(p.deleted_at)
        self.assertIsNone(p.deleted_by)
