from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from events.models import Enrollment, Event, EventCategory, EventInvitation
from participants.models import Participant
from users.models import User


class EventCategoryTest(TestCase):
    def test_str(self):
        cat = EventCategory.objects.create(name="Programacion")
        self.assertEqual(str(cat), "Programacion")


class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com", full_name="Admin", password="pass"
        )

    def _make_event(self, name="Taller Python", status="active"):
        return Event.objects.create(
            name=name, event_date=date(2026, 6, 15), status=status, created_by=self.user
        )

    def test_str_includes_name_and_date(self):
        event = self._make_event()
        self.assertIn("Taller Python", str(event))
        self.assertIn("15/06/2026", str(event))

    def test_default_status_is_active(self):
        event = self._make_event()
        self.assertEqual(event.status, "active")

    def test_is_active_default_true(self):
        event = self._make_event()
        self.assertTrue(event.is_active)

    def test_auto_send_certificates_default_false(self):
        event = self._make_event()
        self.assertFalse(event.auto_send_certificates)

    def test_valid_status_choices(self):
        for status in ["draft", "active", "finished", "cancelled"]:
            e = Event.objects.create(
                name=f"E {status}",
                event_date=date(2026, 1, 1),
                status=status,
                created_by=self.user,
            )
            self.assertEqual(e.status, status)


class EventInvitationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com", full_name="Admin", password="pass"
        )
        self.event = Event.objects.create(
            name="Evento Test", event_date=date(2026, 6, 1), created_by=self.user
        )

    def test_is_expired_when_past(self):
        inv = EventInvitation.objects.create(
            event=self.event,
            email="test@test.com",
            expires_at=timezone.now() - timedelta(hours=1),
            created_by=self.user,
        )
        self.assertTrue(inv.is_expired())

    def test_is_not_expired_when_future(self):
        inv = EventInvitation.objects.create(
            event=self.event,
            email="future@test.com",
            expires_at=timezone.now() + timedelta(days=7),
            created_by=self.user,
        )
        self.assertFalse(inv.is_expired())

    def test_is_not_expired_when_no_expiry(self):
        inv = EventInvitation.objects.create(
            event=self.event, email="noexp@test.com", created_by=self.user
        )
        self.assertFalse(inv.is_expired())

    def test_default_status_is_pending(self):
        inv = EventInvitation.objects.create(
            event=self.event, email="p@p.com", created_by=self.user
        )
        self.assertEqual(inv.status, "pending")

    def test_tokens_are_unique(self):
        inv1 = EventInvitation.objects.create(
            event=self.event, email="a@a.com", created_by=self.user
        )
        inv2 = EventInvitation.objects.create(
            event=self.event, email="b@b.com", created_by=self.user
        )
        self.assertNotEqual(inv1.token, inv2.token)


class EnrollmentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com", full_name="Admin", password="pass"
        )
        self.participant = Participant.objects.create(
            document_id="99999",
            first_name="Ana",
            last_name="Torres",
            email="ana@test.com",
            created_by=self.user,
        )
        self.event = Event.objects.create(
            name="Curso Test", event_date=date(2026, 5, 1), created_by=self.user
        )

    def test_str_shows_attendance_check(self):
        enr = Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=True,
            created_by=self.user,
        )
        self.assertIn("✓", str(enr))

    def test_str_shows_attendance_cross_when_absent(self):
        enr = Enrollment.objects.create(
            participant=self.participant,
            event=self.event,
            attendance=False,
            created_by=self.user,
        )
        self.assertIn("✗", str(enr))

    def test_unique_participant_event_pair(self):
        Enrollment.objects.create(
            participant=self.participant, event=self.event, created_by=self.user
        )
        with self.assertRaises(Exception):
            Enrollment.objects.create(
                participant=self.participant, event=self.event, created_by=self.user
            )

    def test_attendance_default_false(self):
        enr = Enrollment.objects.create(
            participant=self.participant, event=self.event, created_by=self.user
        )
        self.assertFalse(enr.attendance)


class EventInstructorStrTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com", full_name="Admin", password="pass"
        )
        from instructors.models import Instructor

        self.instructor = Instructor.objects.create(
            full_name="Rosa Diaz",
            specialty="JS",
            email="rosa@test.com",
            created_by=self.user,
        )
        self.event = Event.objects.create(
            name="React Workshop", event_date=date(2026, 7, 1), created_by=self.user
        )

    def test_event_instructor_str(self):
        from events.models import EventInstructor

        ei = EventInstructor.objects.create(
            event=self.event, instructor=self.instructor, created_by=self.user
        )
        s = str(ei)
        self.assertIn("React Workshop", s)
        self.assertIn("Rosa Diaz", s)

    def test_event_invitation_str(self):
        inv = EventInvitation.objects.create(
            event=self.event, email="test@x.com", created_by=self.user
        )
        s = str(inv)
        self.assertIn("test@x.com", s)
        self.assertIn("React Workshop", s)
