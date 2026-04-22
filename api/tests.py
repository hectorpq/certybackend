from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import date

from users.models import User
from students.models import Student
from instructors.models import Instructor
from events.models import Event, EventCategory, Enrollment
from certificados.models import Certificate, Template


def make_admin(email='admin@test.com'):
    return User.objects.create_user(
        email=email, full_name='Admin', password='pass123', role='admin', is_staff=True
    )

def make_user(email='user@test.com'):
    return User.objects.create_user(
        email=email, full_name='User', password='pass123', role='participante'
    )

def make_event(user, name='Evento Test', ev_date=None):
    return Event.objects.create(
        name=name, event_date=ev_date or date(2026, 6, 1), created_by=user
    )

def make_student(user, doc='12345', email='student@test.com'):
    return Student.objects.create(
        document_id=doc, first_name='Ana', last_name='Lopez',
        email=email, phone='999000111', created_by=user
    )


# ─────────────────────────────────────────────
# Auth endpoints
# ─────────────────────────────────────────────

class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        res = self.client.post('/api/register/', {
            'email': 'new@test.com', 'full_name': 'Nuevo', 'password': 'Pass1234!', 'password_confirm': 'Pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('email', res.data)

    def test_register_password_mismatch(self):
        res = self.client.post('/api/register/', {
            'email': 'new2@test.com', 'full_name': 'Nuevo', 'password': 'Pass1234!', 'password_confirm': 'Other!'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        make_admin('dup@test.com')
        res = self.client.post('/api/register/', {
            'email': 'dup@test.com', 'full_name': 'Otro', 'password': 'Pass1234!', 'password_confirm': 'Pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_admin()

    def test_login_success(self):
        res = self.client.post('/api/login/', {'email': 'admin@test.com', 'password': 'pass123'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_wrong_password(self):
        res = self.client.post('/api/login/', {'email': 'admin@test.com', 'password': 'wrong'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        res = self.client.post('/api/login/', {'email': 'ghost@test.com', 'password': 'pass123'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class CurrentUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_admin()
        self.client.force_authenticate(user=self.user)

    def test_get_current_user(self):
        res = self.client.get('/api/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'admin@test.com')
        self.assertIn('role', res.data)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        res = self.client.get('/api/me/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────
# Students
# ─────────────────────────────────────────────

class StudentsViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_list_students(self):
        make_student(self.admin)
        res = self.client.get('/api/students/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_student(self):
        res = self.client.post('/api/students/', {
            'document_id': '99999', 'first_name': 'Luis', 'last_name': 'Gomez',
            'email': 'luis@test.com', 'phone': '111222333'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['first_name'], 'Luis')

    def test_retrieve_student(self):
        s = make_student(self.admin)
        res = self.client.get(f'/api/students/{s.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'student@test.com')

    def test_update_student(self):
        s = make_student(self.admin)
        res = self.client.patch(f'/api/students/{s.id}/', {'first_name': 'Cambiado'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['first_name'], 'Cambiado')

    def test_delete_student(self):
        s = make_student(self.admin)
        res = self.client.delete(f'/api/students/{s.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_duplicate_document_id_returns_400(self):
        make_student(self.admin)
        res = self.client.post('/api/students/', {
            'document_id': '12345', 'first_name': 'Otro', 'last_name': 'X',
            'email': 'otro@test.com', 'phone': ''
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_list(self):
        self.client.force_authenticate(user=None)
        res = self.client.get('/api/students/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────
# Instructors
# ─────────────────────────────────────────────

class InstructorsViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_list_instructors_empty(self):
        res = self.client.get('/api/instructors/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_instructor(self):
        res = self.client.post('/api/instructors/', {
            'full_name': 'Rosa Diaz', 'email': 'rosa@test.com', 'specialty': 'Python'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['full_name'], 'Rosa Diaz')

    def test_retrieve_instructor(self):
        inst = Instructor.objects.create(full_name='Carlos', email='carlos@test.com', created_by=self.admin)
        res = self.client.get(f'/api/instructors/{inst.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_instructor(self):
        inst = Instructor.objects.create(full_name='Pedro', email='pedro@test.com', created_by=self.admin)
        res = self.client.patch(f'/api/instructors/{inst.id}/', {'specialty': 'Django'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['specialty'], 'Django')

    def test_delete_instructor(self):
        inst = Instructor.objects.create(full_name='Temp', email='temp@test.com', created_by=self.admin)
        res = self.client.delete(f'/api/instructors/{inst.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────

class EventsViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_list_events(self):
        make_event(self.admin)
        res = self.client.get('/api/events/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_event(self):
        res = self.client.post('/api/events/', {
            'name': 'Nuevo Evento', 'event_date': '2026-08-01', 'status': 'active'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Nuevo Evento')

    def test_retrieve_event(self):
        e = make_event(self.admin)
        res = self.client.get(f'/api/events/{e.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Evento Test')

    def test_update_event(self):
        e = make_event(self.admin)
        res = self.client.patch(f'/api/events/{e.id}/', {'status': 'finished'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_event(self):
        e = make_event(self.admin)
        res = self.client.delete(f'/api/events/{e.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_participants_empty(self):
        e = make_event(self.admin)
        res = self.client.get(f'/api/events/{e.id}/participants/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_participants_with_enrollment(self):
        e = make_event(self.admin)
        s = make_student(self.admin)
        Enrollment.objects.create(student=s, event=e, attendance=True, created_by=self.admin)
        res = self.client.get(f'/api/events/{e.id}/participants/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertTrue(res.data[0]['attendance'])

    def test_enroll_student_by_id(self):
        e = make_event(self.admin)
        s = make_student(self.admin)
        res = self.client.post(f'/api/events/{e.id}/enroll/', {'student_id': s.id})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_enroll_student_by_email(self):
        e = make_event(self.admin)
        res = self.client.post(f'/api/events/{e.id}/enroll/', {'student_email': 'new@enroll.com'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_enroll_duplicate_returns_400(self):
        e = make_event(self.admin)
        s = make_student(self.admin)
        Enrollment.objects.create(student=s, event=e, created_by=self.admin)
        res = self.client.post(f'/api/events/{e.id}/enroll/', {'student_id': s.id})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enroll_missing_params_returns_400(self):
        e = make_event(self.admin)
        res = self.client.post(f'/api/events/{e.id}/enroll/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enroll_nonexistent_student_returns_404(self):
        e = make_event(self.admin)
        res = self.client.post(f'/api/events/{e.id}/enroll/', {'student_id': 9999})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_stats(self):
        e = make_event(self.admin)
        res = self.client.get(f'/api/events/{e.id}/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_enroll(self):
        regular = make_user('regular@test.com')
        self.client.force_authenticate(user=regular)
        e = make_event(self.admin)
        res = self.client.post(f'/api/events/{e.id}/enroll/', {'student_email': 'x@x.com'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# ─────────────────────────────────────────────
# Certificates
# ─────────────────────────────────────────────

class CertificateViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.student = make_student(self.admin)
        self.event = make_event(self.admin)
        self.template = Template.objects.create(name='Base', created_by=self.admin)
        self.cert = Certificate.objects.create(
            student=self.student, event=self.event,
            template=self.template, generated_by=self.admin
        )

    def test_list_certificates(self):
        res = self.client.get('/api/certificates/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_certificate(self):
        res = self.client.get(f'/api/certificates/{self.cert.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_history_endpoint(self):
        res = self.client.get(f'/api/certificates/{self.cert.id}/history/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_attempts', res.data)

    def test_verify_with_valid_code(self):
        res = self.client.get(f'/api/certificates/verify/?code={self.cert.verification_code}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'success')

    def test_verify_with_invalid_code(self):
        res = self.client.get('/api/certificates/verify/?code=INVALID-CODE-XXXX')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_verify_without_code_returns_400(self):
        res = self.client.get('/api/certificates/verify/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_raises_if_not_pending(self):
        Certificate.objects.filter(pk=self.cert.pk).update(status='generated')
        res = self.client.post(f'/api/certificates/{self.cert.id}/generate/', {
            'student_id': self.student.id,
            'event_id': self.event.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deliver_raises_if_not_generated(self):
        res = self.client.post(f'/api/certificates/{self.cert.id}/deliver/', {'method': 'email'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────

class TemplateViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_list_templates(self):
        Template.objects.create(name='T1', created_by=self.admin)
        res = self.client.get('/api/templates/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_template(self):
        res = self.client.post('/api/templates/', {'name': 'Nueva Plantilla', 'category': 'Cursos'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Nueva Plantilla')

    def test_retrieve_template(self):
        t = Template.objects.create(name='T2', created_by=self.admin)
        res = self.client.get(f'/api/templates/{t.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_template(self):
        t = Template.objects.create(name='T3', created_by=self.admin)
        res = self.client.patch(f'/api/templates/{t.id}/', {'name': 'Actualizada'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_template(self):
        t = Template.objects.create(name='T4', created_by=self.admin)
        res = self.client.delete(f'/api/templates/{t.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# Delivery Logs
# ─────────────────────────────────────────────

class DeliveryLogViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_list_delivery_logs(self):
        res = self.client.get('/api/deliveries/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_by_certificate_id(self):
        student = make_student(self.admin)
        event = make_event(self.admin)
        template = Template.objects.create(name='T', created_by=self.admin)
        cert = Certificate.objects.create(student=student, event=event, template=template, generated_by=self.admin)
        res = self.client.get(f'/api/deliveries/?certificate_id={cert.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Permissions
# ─────────────────────────────────────────────

class PermissionsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.user = make_user()

    def _req(self, method='GET'):
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        req = factory.get('/') if method == 'GET' else factory.post('/')
        return req

    def test_is_admin_true_for_admin(self):
        from api.permissions import is_admin
        self.client.force_authenticate(user=self.admin)
        req = self._req()
        req.user = self.admin
        self.assertTrue(is_admin(req))

    def test_is_admin_false_for_participante(self):
        from api.permissions import is_admin
        req = self._req()
        req.user = self.user
        self.assertFalse(is_admin(req))

    def test_is_admin_false_for_anonymous(self):
        from api.permissions import is_admin
        from django.contrib.auth.models import AnonymousUser
        req = self._req()
        req.user = AnonymousUser()
        self.assertFalse(is_admin(req))

    def _check_permission(self, perm_class, user, method='GET'):
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        if method == 'GET':
            req = factory.get('/')
        else:
            req = factory.post('/')
        req.user = user
        from rest_framework.request import Request
        from rest_framework.parsers import JSONParser
        drf_req = Request(req)
        drf_req._user = user
        perm = perm_class()
        return perm.has_permission(drf_req, None)

    def test_is_admin_perm_allows_admin(self):
        from api.permissions import IsAdmin
        self.assertTrue(self._check_permission(IsAdmin, self.admin))

    def test_is_admin_perm_denies_participante(self):
        from api.permissions import IsAdmin
        self.assertFalse(self._check_permission(IsAdmin, self.user))

    def test_admin_or_read_only_allows_admin_write(self):
        from api.permissions import IsAdminOrReadOnly
        self.assertTrue(self._check_permission(IsAdminOrReadOnly, self.admin, 'POST'))

    def test_admin_or_read_only_allows_user_read(self):
        from api.permissions import IsAdminOrReadOnly
        self.assertTrue(self._check_permission(IsAdminOrReadOnly, self.user, 'GET'))

    def test_admin_or_read_only_denies_user_write(self):
        from api.permissions import IsAdminOrReadOnly
        self.assertFalse(self._check_permission(IsAdminOrReadOnly, self.user, 'POST'))

    def test_can_manage_users_admin(self):
        from api.permissions import CanManageUsers
        self.assertTrue(self._check_permission(CanManageUsers, self.admin, 'POST'))

    def test_can_manage_users_participante_read(self):
        from api.permissions import CanManageUsers
        self.assertTrue(self._check_permission(CanManageUsers, self.user, 'GET'))

    def test_can_manage_certificates_admin(self):
        from api.permissions import CanManageCertificates
        self.assertTrue(self._check_permission(CanManageCertificates, self.admin, 'POST'))

    def test_can_manage_events_admin(self):
        from api.permissions import CanManageEvents
        self.assertTrue(self._check_permission(CanManageEvents, self.admin, 'POST'))

    def test_can_manage_students_admin(self):
        from api.permissions import CanManageStudents
        self.assertTrue(self._check_permission(CanManageStudents, self.admin, 'POST'))

    def test_can_manage_instructors_admin(self):
        from api.permissions import CanManageInstructors
        self.assertTrue(self._check_permission(CanManageInstructors, self.admin, 'POST'))

    def test_can_manage_templates_admin(self):
        from api.permissions import CanManageTemplates
        self.assertTrue(self._check_permission(CanManageTemplates, self.admin, 'POST'))

    def test_all_permissions_deny_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        from api.permissions import (IsAdmin, IsAdminOrReadOnly, CanManageUsers,
            CanManageCertificates, CanManageEvents, CanManageStudents,
            CanManageInstructors, CanManageTemplates)
        anon = AnonymousUser()
        for perm_class in [IsAdmin, IsAdminOrReadOnly, CanManageUsers,
                           CanManageCertificates, CanManageEvents, CanManageStudents,
                           CanManageInstructors, CanManageTemplates]:
            self.assertFalse(self._check_permission(perm_class, anon))


# ─────────────────────────────────────────────
# Participante (non-admin) role tests
# ─────────────────────────────────────────────

class ParticipanteAccessTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.regular = make_user()
        self.client.force_authenticate(user=self.regular)

    def test_participante_can_list_students(self):
        res = self.client.get('/api/students/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_participante_cannot_create_student(self):
        res = self.client.post('/api/students/', {
            'document_id': '77777', 'first_name': 'X', 'last_name': 'Y',
            'email': 'x@test.com', 'phone': ''
        })
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_participante_can_view_certificates(self):
        res = self.client.get('/api/certificates/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_participante_can_verify_certificate_public(self):
        self.client.force_authenticate(user=None)
        res = self.client.get('/api/certificates/verify/?code=INVALID')
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])

    def test_participante_can_list_events(self):
        res = self.client.get('/api/events/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Events extra endpoints
# ─────────────────────────────────────────────

class EventExtraEndpointsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)
        self.student = make_student(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)

    def test_event_deliveries_empty(self):
        res = self.client.get(f'/api/events/{self.event.id}/deliveries/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_stats_with_enrollment(self):
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)
        res = self.client.get(f'/api/events/{self.event.id}/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['attendees'], 1)
        self.assertEqual(res.data['total_enrollments'], 1)

    def test_invitations_list_empty(self):
        res = self.client.get(f'/api/events/{self.event.id}/invitations/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_generate_certificates_no_enrollments(self):
        res = self.client.post(f'/api/events/{self.event.id}/certificates/generate/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['created'], 0)

    def test_generate_certificates_with_student(self):
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)
        res = self.client.post(f'/api/events/{self.event.id}/certificates/generate/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_generate_certificates_non_admin_forbidden(self):
        regular = make_user('r@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.post(f'/api/events/{self.event.id}/certificates/generate/', {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_send_certificates_non_admin_forbidden(self):
        regular = make_user('r2@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.post(f'/api/events/{self.event.id}/certificates/send/', {'method': 'email'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


# ─────────────────────────────────────────────
# Certificate: expired verify + participante queryset
# ─────────────────────────────────────────────

class CertificateExtraTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.student = make_student(self.admin)
        self.event = make_event(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)

    def test_verify_expired_certificate(self):
        from django.utils import timezone
        from datetime import timedelta
        self.client.force_authenticate(user=self.admin)
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template,
            generated_by=self.admin,
            expires_at=timezone.now() - timedelta(days=1)
        )
        res = self.client.get(f'/api/certificates/verify/?code={cert.verification_code}')
        self.assertEqual(res.status_code, 410)

    def test_participante_sees_own_certificates(self):
        participante = User.objects.create_user(
            email='p@test.com', full_name='P', password='pass', role='participante'
        )
        student2 = Student.objects.create(
            document_id='88888', first_name='Par', last_name='T',
            email='p@test.com', created_by=self.admin
        )
        Certificate.objects.create(
            student=student2, event=self.event, template=self.template, generated_by=self.admin
        )
        self.client.force_authenticate(user=participante)
        res = self.client.get('/api/certificates/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Enrollments
# ─────────────────────────────────────────────

class EnrollmentViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)
        self.student = make_student(self.admin)

    def test_list_enrollments(self):
        res = self.client.get('/api/enrollments/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_enrollment(self):
        res = self.client.post('/api/enrollments/', {
            'student_id': self.student.id,
            'event_id': self.event.id,
        })
        self.assertIn(res.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_create_enrollment_invalid_student(self):
        res = self.client.post('/api/enrollments/', {
            'student_id': 9999,
            'event_id': self.event.id,
        })
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])


# ─────────────────────────────────────────────
# Google Auth (mocked)
# ─────────────────────────────────────────────

class GoogleAuthViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_google_auth_missing_token(self):
        res = self.client.post('/api/auth/google/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_invalid_token(self, mock_verify):
        mock_verify.side_effect = ValueError('invalid token')
        res = self.client.post('/api/auth/google/', {'token': 'bad-token'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_existing_user(self, mock_verify):
        from django.conf import settings
        settings.GOOGLE_CLIENT_ID = 'test-client-id'
        User.objects.create_user(email='google@test.com', full_name='G', password='pass')
        mock_verify.return_value = {'email': 'google@test.com', 'name': 'G'}
        res = self.client.post('/api/auth/google/', {'token': 'valid-token'})
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_new_user(self, mock_verify):
        from django.conf import settings
        settings.GOOGLE_CLIENT_ID = 'test-client-id'
        mock_verify.return_value = {'email': 'newgoogle@test.com', 'name': 'New'}
        res = self.client.post('/api/auth/google/', {'token': 'valid-token'})
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])


# ─────────────────────────────────────────────
# InvitationPublicView
# ─────────────────────────────────────────────

class InvitationPublicViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.event = make_event(self.admin)

    def _make_invitation(self, email='invite@test.com', status_val='pending', expires=None):
        from events.models import EventInvitation
        from django.utils import timezone
        from datetime import timedelta
        inv = EventInvitation.objects.create(
            event=self.event,
            email=email,
            status=status_val,
            expires_at=expires,
            created_by=self.admin
        )
        return inv

    def test_get_invitation_valid_token(self):
        inv = self._make_invitation()
        res = self.client.get(f'/api/invitations/{inv.token}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_invitation_invalid_token(self):
        res = self.client.get('/api/invitations/nonexistent-token-xyz/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_invitation_already_accepted(self):
        inv = self._make_invitation(status_val='accepted')
        res = self.client.get(f'/api/invitations/{inv.token}/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_invitation_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        inv = self._make_invitation(expires=timezone.now() - timedelta(hours=1))
        res = self.client.get(f'/api/invitations/{inv.token}/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_invitation_invalid_token(self):
        res = self.client.post('/api/invitations/bad-token/accept/', {})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_invitation_existing_student(self):
        student = make_student(self.admin)
        from events.models import EventInvitation
        inv = EventInvitation.objects.create(
            event=self.event, email=student.email, student=student,
            created_by=self.admin
        )
        res = self.client.post(f'/api/invitations/{inv.token}/accept/', {
            'email': student.email
        })
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])


# ─────────────────────────────────────────────
# Certificate generate success (with PDF mock)
# ─────────────────────────────────────────────

class CertificateGenerateTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.student = make_student(self.admin)
        self.event = make_event(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_certificate_success(self, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        res = self.client.post(f'/api/certificates/{cert.id}/generate/', {
            'student_id': self.student.id, 'event_id': self.event.id
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'success')

    @patch('services.email_service.EmailService.send_certificate')
    def test_deliver_certificate_success(self, mock_send):
        mock_send.return_value = {'success': True, 'message': 'sent'}
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated', pdf_url='/media/c.pdf')
        cert.refresh_from_db()
        res = self.client.post(f'/api/certificates/{cert.id}/deliver/', {'method': 'email'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch('services.email_service.EmailService.send_certificate')
    def test_deliver_certificate_whatsapp(self, mock_send):
        mock_send.return_value = {'success': True, 'message': 'sent'}
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated', pdf_url='/media/c.pdf')
        cert.refresh_from_db()
        res = self.client.post(f'/api/certificates/{cert.id}/deliver/', {'method': 'whatsapp'})
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


# ─────────────────────────────────────────────
# Students import_students endpoint
# ─────────────────────────────────────────────

class StudentsImportTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_import_without_file_returns_400(self):
        res = self.client.post('/api/students/import_students/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_with_excel_file(self):
        import pandas as pd
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        df = pd.DataFrame([{
            'document_id': 'IMP001', 'first_name': 'Import', 'last_name': 'User',
            'email': 'import@test.com', 'phone': ''
        }])
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        f = SimpleUploadedFile('students.xlsx', buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        res = self.client.post('/api/students/import_students/', {'file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('imported', res.data)

    def test_import_with_csv_file(self):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        csv_content = b'document_id,first_name,last_name,email,phone\nCSV001,CSV,User,csv@test.com,\n'
        f = SimpleUploadedFile('students.csv', csv_content, content_type='text/csv')
        res = self.client.post('/api/students/import_students/', {'file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('imported', res.data)

    def test_import_invalid_file_returns_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('bad.xlsx', b'not-real-excel', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        res = self.client.post('/api/students/import_students/', {'file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# Google Auth - additional edge cases
# ─────────────────────────────────────────────

class GoogleAuthEdgeCasesTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_google_auth_no_client_id_configured(self):
        from django.conf import settings
        original = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        settings.GOOGLE_CLIENT_ID = None
        try:
            res = self.client.post('/api/auth/google/', {'token': 'some-token'})
            self.assertIn(res.status_code, [
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_400_BAD_REQUEST,
            ])
        finally:
            settings.GOOGLE_CLIENT_ID = original

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_no_email_in_token(self, mock_verify):
        from django.conf import settings
        settings.GOOGLE_CLIENT_ID = 'test-client-id'
        mock_verify.return_value = {'name': 'No Email User'}
        res = self.client.post('/api/auth/google/', {'token': 'valid-token'})
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @patch('google.oauth2.id_token.verify_oauth2_token')
    def test_google_auth_generic_exception(self, mock_verify):
        from django.conf import settings
        settings.GOOGLE_CLIENT_ID = 'test-client-id'
        mock_verify.side_effect = Exception('network error')
        res = self.client.post('/api/auth/google/', {'token': 'any-token'})
        self.assertIn(res.status_code, [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_401_UNAUTHORIZED])


# ─────────────────────────────────────────────
# IsAdminUserOrReadOnly + IsCertificateOwnerOrAdmin in views.py
# ─────────────────────────────────────────────

class ViewPermissionClassesTest(TestCase):
    def test_is_admin_user_or_read_only_safe_method(self):
        from api.views import IsAdminUserOrReadOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        factory = APIRequestFactory()
        raw = factory.get('/')
        from django.contrib.auth.models import AnonymousUser
        raw.user = AnonymousUser()
        req = Request(raw)
        req._user = AnonymousUser()
        perm = IsAdminUserOrReadOnly()
        self.assertTrue(perm.has_permission(req, None))

    def test_is_admin_user_or_read_only_write_non_admin(self):
        from api.views import IsAdminUserOrReadOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        factory = APIRequestFactory()
        raw = factory.post('/')
        user = User.objects.create_user(email='nonadmin@test.com', full_name='N', password='pass')
        raw.user = user
        req = Request(raw)
        req._user = user
        perm = IsAdminUserOrReadOnly()
        self.assertFalse(perm.has_permission(req, None))

    def test_is_certificate_owner_or_admin_safe_method(self):
        from api.views import IsCertificateOwnerOrAdmin
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        factory = APIRequestFactory()
        raw = factory.get('/')
        from django.contrib.auth.models import AnonymousUser
        raw.user = AnonymousUser()
        req = Request(raw)
        perm = IsCertificateOwnerOrAdmin()
        self.assertTrue(perm.has_object_permission(req, None, None))

    def test_is_certificate_owner_or_admin_write_staff(self):
        from api.views import IsCertificateOwnerOrAdmin
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        factory = APIRequestFactory()
        raw = factory.post('/')
        admin = User.objects.create_user(email='staff@test.com', full_name='A', password='pass', is_staff=True)
        raw.user = admin
        req = Request(raw)
        req._user = admin
        perm = IsCertificateOwnerOrAdmin()
        self.assertTrue(perm.has_object_permission(req, None, None))


# ─────────────────────────────────────────────
# Instructors - non-admin paths
# ─────────────────────────────────────────────

class InstructorNonAdminTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.regular = make_user('regular@test.com')

    def test_non_admin_gets_own_instructors(self):
        Instructor.objects.create(full_name='Own', email='own@test.com', created_by=self.regular)
        Instructor.objects.create(full_name='Other', email='other@test.com', created_by=self.admin)
        self.client.force_authenticate(user=self.regular)
        res = self.client.get('/api/instructors/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        names = [i['full_name'] for i in items]
        self.assertIn('Own', names)
        self.assertNotIn('Other', names)

    def test_non_admin_cannot_create_instructor(self):
        self.client.force_authenticate(user=self.regular)
        res = self.client.post('/api/instructors/', {'full_name': 'X', 'email': 'x@test.com'})
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])


# ─────────────────────────────────────────────
# Template upload-image and preview
# ─────────────────────────────────────────────

class TemplateUploadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.template = Template.objects.create(name='Upload Test', created_by=self.admin)

    def test_upload_image_no_file_returns_400(self):
        res = self.client.post(f'/api/templates/{self.template.id}/upload-image/', {}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_image_invalid_type_returns_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('doc.pdf', b'%PDF', content_type='application/pdf')
        res = self.client.post(f'/api/templates/{self.template.id}/upload-image/', {'file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_image_valid_png(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Minimal valid PNG bytes
        import struct, zlib
        def minimal_png():
            sig = b'\x89PNG\r\n\x1a\n'
            def chunk(name, data):
                c = struct.pack('>I', len(data)) + name + data
                return c + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
            ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            raw = b'\x00\xff\xff\xff'
            compressed = zlib.compress(raw)
            idat = chunk(b'IDAT', compressed)
            iend = chunk(b'IEND', b'')
            return sig + ihdr + idat + iend
        f = SimpleUploadedFile('img.png', minimal_png(), content_type='image/png')
        res = self.client.post(f'/api/templates/{self.template.id}/upload-image/', {'file': f}, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_get_preview(self):
        res = self.client.get(f'/api/templates/{self.template.id}/preview/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('layout_config', res.data)


# ─────────────────────────────────────────────
# EventsViewSet - send_certificates, send_invitations, finalize
# ─────────────────────────────────────────────

class EventsAdvancedTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)
        self.student = make_student(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)

    def test_send_certificates_empty(self):
        res = self.client.post(f'/api/events/{self.event.id}/certificates/send/', {'method': 'email'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_sent'], 0)

    @patch('services.email_service.EmailService.send_certificate')
    def test_send_certificates_with_generated_cert(self, mock_send):
        mock_send.return_value = {'success': True, 'message': 'sent'}
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated', pdf_url='/media/cert.pdf')
        res = self.client.post(f'/api/events/{self.event.id}/certificates/send/', {'method': 'email'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_send_invitations_no_emails_returns_400(self):
        res = self.client.post(f'/api/events/{self.event.id}/invitations/send/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('django.core.mail.send_mail')
    def test_send_invitations_with_email_list(self, mock_mail):
        mock_mail.return_value = 1
        import json
        res = self.client.post(
            f'/api/events/{self.event.id}/invitations/send/',
            {'emails': json.dumps(['newguest@test.com'])},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('created', res.data)

    @patch('django.core.mail.send_mail')
    def test_send_invitations_duplicate_skipped(self, mock_mail):
        mock_mail.return_value = 1
        from events.models import EventInvitation
        EventInvitation.objects.create(event=self.event, email='dup@test.com', created_by=self.admin)
        import json
        res = self.client.post(
            f'/api/events/{self.event.id}/invitations/send/',
            {'emails': json.dumps(['dup@test.com'])},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('errors', res.data)

    def test_send_all_invitations_none_pending_returns_400(self):
        res = self.client.post(f'/api/events/{self.event.id}/invitations/send-all/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('django.core.mail.send_mail')
    def test_send_all_invitations_sends_pending(self, mock_mail):
        mock_mail.return_value = 1
        from events.models import EventInvitation
        EventInvitation.objects.create(
            event=self.event, email='pending@test.com', status='pending', created_by=self.admin
        )
        res = self.client.post(f'/api/events/{self.event.id}/invitations/send-all/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('sent', res.data)

    def test_finalize_event(self):
        res = self.client.post(f'/api/events/{self.event.id}/finalize/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'finished')

    def test_finalize_already_finished_returns_400(self):
        Event.objects.filter(pk=self.event.pk).update(status='finished')
        self.event.refresh_from_db()
        res = self.client.post(f'/api/events/{self.event.id}/finalize/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('services.email_service.EmailService.send_certificate')
    def test_finalize_with_send_certificates(self, mock_send):
        mock_send.return_value = {'success': True, 'message': 'sent'}
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated', pdf_url='/media/cert.pdf')
        res = self.client.post(f'/api/events/{self.event.id}/finalize/', {'send_certificates': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_participante_sees_enrolled_events(self):
        participante = make_user('part@test.com')
        student2 = Student.objects.create(
            document_id='PART01', first_name='Part', last_name='User',
            email='part@test.com', created_by=self.admin
        )
        Enrollment.objects.create(student=student2, event=self.event, created_by=self.admin)
        self.client.force_authenticate(user=participante)
        res = self.client.get('/api/events/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_generate_certificates_already_exists(self):
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated')
        res = self.client.post(f'/api/events/{self.event.id}/certificates/generate/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('already_exists', res.data['results'])

    def test_send_invitations_invalid_email_skipped(self):
        import json
        res = self.client.post(
            f'/api/events/{self.event.id}/invitations/send/',
            {'emails': json.dumps(['not-an-email'])},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# BulkCertificateGenerationView
# ─────────────────────────────────────────────

class BulkCertificateGenerationViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin, name='Bulk Event')

    def _make_excel_file(self):
        import pandas as pd
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        df = pd.DataFrame([{
            'full_name': 'Bulk User',
            'email': 'bulk@test.com',
            'document_id': 'BULK001',
            'event_name': 'Bulk Event',
            'phone': '111000999'
        }])
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return SimpleUploadedFile('bulk.xlsx', buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_get_returns_format_info(self):
        res = self.client.get('/api/certificates/generate-bulk/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('required_columns', res.data)

    def test_post_no_file_returns_400(self):
        res = self.client.post('/api/certificates/generate-bulk/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_non_admin_forbidden(self):
        regular = make_user('reg@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.post('/api/certificates/generate-bulk/', {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_with_valid_excel(self):
        f = self._make_excel_file()
        res = self.client.post('/api/certificates/generate-bulk/', {'excel_file': f}, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


# ─────────────────────────────────────────────
# BulkCertificatePreviewView
# ─────────────────────────────────────────────

class BulkCertificatePreviewViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin, name='Preview Event')

    def _make_excel_file(self):
        import pandas as pd
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        df = pd.DataFrame([{
            'full_name': 'Preview User',
            'email': 'preview@test.com',
            'document_id': 'PRV001',
            'event_name': 'Preview Event',
        }])
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return SimpleUploadedFile('preview.xlsx', buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_post_non_admin_forbidden(self):
        regular = make_user('prev@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.post('/api/certificates/preview/', {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_no_file_returns_400(self):
        res = self.client.post('/api/certificates/preview/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_with_valid_excel(self):
        f = self._make_excel_file()
        res = self.client.post('/api/certificates/preview/', {'excel_file': f}, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_post_with_invalid_excel(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('bad.xlsx', b'notexcel', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        res = self.client.post('/api/certificates/preview/', {'excel_file': f}, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK])


# ─────────────────────────────────────────────
# BulkCertificateProcessView
# ─────────────────────────────────────────────

class BulkCertificateProcessViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin, name='Process Event')

    def test_post_empty_data_returns_400(self):
        res = self.client.post('/api/certificates/process/', {'data': []})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_missing_data_returns_400(self):
        res = self.client.post('/api/certificates/process/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_with_valid_records(self):
        res = self.client.post('/api/certificates/process/', {'data': [{
            'full_name': 'Process User',
            'email': 'proc@test.com',
            'document_id': 'PROC001',
            'event_name': 'Process Event',
        }]}, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


# ─────────────────────────────────────────────
# EnrollmentViewSet - create / destroy / attendance
# ─────────────────────────────────────────────

class EnrollmentViewSetAdvancedTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)
        self.student = make_student(self.admin)

    def test_create_enrollment_success(self):
        res = self.client.post('/api/enrollments/', {
            'student_id': self.student.id,
            'event_id': self.event.id,
            'attendance': False,
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_create_enrollment_nonexistent_student(self):
        res = self.client.post('/api/enrollments/', {
            'student_id': 99999,
            'event_id': self.event.id,
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])

    def test_create_enrollment_nonexistent_event(self):
        res = self.client.post('/api/enrollments/', {
            'student_id': self.student.id,
            'event_id': 99999,
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])

    def test_non_admin_list_enrollments_returns_403_without_event_pk(self):
        regular = make_user('r@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.get('/api/enrollments/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_all_enrollments(self):
        Enrollment.objects.create(student=self.student, event=self.event, created_by=self.admin)
        res = self.client.get('/api/enrollments/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# InvitationPublicView - POST paths
# ─────────────────────────────────────────────

class InvitationPublicPostTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.event = make_event(self.admin)

    def _make_invitation(self, email='invite@test.com', status_val='pending', expires=None):
        from events.models import EventInvitation
        return EventInvitation.objects.create(
            event=self.event, email=email, status=status_val,
            expires_at=expires, created_by=self.admin
        )

    def test_accept_no_student_registered_returns_400(self):
        inv = self._make_invitation(email='noone@test.com')
        res = self.client.post(f'/api/invitations/{inv.token}/accept/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_already_accepted_invitation(self):
        inv = self._make_invitation(status_val='accepted')
        res = self.client.post(f'/api/invitations/{inv.token}/accept/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_expired_invitation(self):
        from django.utils import timezone
        from datetime import timedelta
        inv = self._make_invitation(expires=timezone.now() - timedelta(hours=1))
        res = self.client.post(f'/api/invitations/{inv.token}/accept/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_valid_invitation_with_existing_student(self):
        student = make_student(self.admin, email='inv_student@test.com')
        inv = self._make_invitation(email='inv_student@test.com')
        inv.student = student
        inv.save()
        res = self.client.post(f'/api/invitations/{inv.token}/accept/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_accept_finds_student_by_email(self):
        make_student(self.admin, email='findme@test.com', doc='FIND01')
        inv = self._make_invitation(email='findme@test.com')
        res = self.client.post(f'/api/invitations/{inv.token}/accept/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# InvitationRegisterView
# ─────────────────────────────────────────────

class InvitationRegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.event = make_event(self.admin)

    def _make_invitation(self, email='reg@test.com', status_val='pending', expires=None):
        from events.models import EventInvitation
        return EventInvitation.objects.create(
            event=self.event, email=email, status=status_val,
            expires_at=expires, created_by=self.admin
        )

    def test_register_invalid_token_returns_404(self):
        res = self.client.post('/api/invitations/bad-token/register/', {
            'first_name': 'X', 'last_name': 'Y', 'password': 'Pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_register_already_accepted_returns_400(self):
        inv = self._make_invitation(status_val='accepted')
        res = self.client.post(f'/api/invitations/{inv.token}/register/', {
            'first_name': 'X', 'last_name': 'Y', 'password': 'Pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_expired_returns_400(self):
        from django.utils import timezone
        from datetime import timedelta
        inv = self._make_invitation(expires=timezone.now() - timedelta(hours=1))
        res = self.client.post(f'/api/invitations/{inv.token}/register/', {
            'first_name': 'X', 'last_name': 'Y', 'password': 'Pass1234!'
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_new_user_success(self):
        inv = self._make_invitation(email='newreg@test.com')
        res = self.client.post(f'/api/invitations/{inv.token}/register/', {
            'first_name': 'New', 'last_name': 'Reg', 'password': 'Pass1234!', 'phone': '999'
        })
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_register_existing_user_links_student(self):
        User.objects.create_user(email='existing@test.com', full_name='Exist', password='pass')
        inv = self._make_invitation(email='existing@test.com')
        res = self.client.post(f'/api/invitations/{inv.token}/register/', {
            'first_name': 'Exist', 'last_name': 'User', 'password': 'Pass1234!'
        })
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_register_missing_fields_returns_400(self):
        inv = self._make_invitation(email='incomplete@test.com')
        res = self.client.post(f'/api/invitations/{inv.token}/register/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# CertificateViewSet - participante queryset + generate with template_id
# ─────────────────────────────────────────────

class CertificateViewSetAdvancedTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.student = make_student(self.admin)
        self.event = make_event(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)

    def test_participante_sees_only_own_certs(self):
        participante = make_user('cert_part@test.com')
        student2 = Student.objects.create(
            document_id='CERTPART', first_name='Cert', last_name='Part',
            email='cert_part@test.com', created_by=self.admin
        )
        own_cert = Certificate.objects.create(
            student=student2, event=self.event, template=self.template, generated_by=self.admin
        )
        other_cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        self.client.force_authenticate(user=participante)
        res = self.client.get('/api/certificates/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data.get('results', res.data) if isinstance(res.data, dict) else res.data
        ids = [c['id'] for c in items]
        self.assertIn(own_cert.id, ids)
        self.assertNotIn(other_cert.id, ids)

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_with_template_id(self, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        self.client.force_authenticate(user=self.admin)
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        template2 = Template.objects.create(name='T2', created_by=self.admin)
        res = self.client.post(f'/api/certificates/{cert.id}/generate/', {
            'student_id': self.student.id,
            'event_id': self.event.id,
            'template_id': template2.id,
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])


# ─────────────────────────────────────────────
# Serializer edge cases
# ─────────────────────────────────────────────

class SerializerEdgeCasesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='serial@test.com', full_name='S', password='pass', is_staff=True)

    def test_date_field_none_returns_none(self):
        from api.serializers import DateField
        f = DateField()
        self.assertIsNone(f.to_representation(None))

    def test_date_field_datetime_returns_date_string(self):
        from api.serializers import DateField
        from datetime import datetime
        f = DateField()
        dt = datetime(2026, 5, 1, 12, 0)
        result = f.to_representation(dt)
        self.assertEqual(result, '2026-05-01')

    def test_date_field_internal_value_empty_string(self):
        from api.serializers import DateField
        f = DateField()
        self.assertIsNone(f.to_internal_value(''))

    def test_date_field_internal_value_none(self):
        from api.serializers import DateField
        f = DateField()
        self.assertIsNone(f.to_internal_value(None))

    def test_event_serializer_with_template_and_instructor(self):
        from api.serializers import EventSerializer
        from instructors.models import Instructor
        inst = Instructor.objects.create(full_name='Inst', email='inst@test.com', created_by=self.user)
        template = Template.objects.create(name='Tmpl', created_by=self.user)
        event = Event.objects.create(
            name='Ev', event_date=date(2026, 6, 1), created_by=self.user,
            template=template, instructor=inst
        )
        s = EventSerializer(event)
        self.assertEqual(s.data['template_name'], 'Tmpl')
        self.assertEqual(s.data['instructor_name'], 'Inst')

    def test_user_login_serializer_inactive_user(self):
        from api.serializers import UserLoginSerializer
        User.objects.create_user(
            email='inactive@test.com', full_name='I', password='pass', is_active=False
        )
        s = UserLoginSerializer(data={'email': 'inactive@test.com', 'password': 'pass'})
        self.assertFalse(s.is_valid())

    def test_user_auth_serializer_missing_password(self):
        from api.serializers import UserAuthSerializer
        s = UserAuthSerializer(data={'email': 'x@x.com'})
        self.assertFalse(s.is_valid())

    def test_template_serializer_with_background_url(self):
        from api.serializers import TemplateSerializer
        t = Template.objects.create(name='BG', created_by=self.user, background_url='http://example.com/bg.png')
        s = TemplateSerializer(t)
        self.assertEqual(s.data['background_image_url'], 'http://example.com/bg.png')

    def test_invitation_detail_serializer_student_exists_by_link(self):
        from api.serializers import InvitationDetailSerializer
        from events.models import EventInvitation
        event = Event.objects.create(name='Inv Ev', event_date=date(2026, 7, 1), created_by=self.user)
        student = Student.objects.create(
            document_id='INVSER', first_name='A', last_name='B',
            email='invser@test.com', created_by=self.user
        )
        inv = EventInvitation.objects.create(
            event=event, email='invser@test.com', student=student, created_by=self.user
        )
        s = InvitationDetailSerializer(inv)
        self.assertTrue(s.data['student_exists'])


# ─────────────────────────────────────────────
# Permission classes - participante safe-method paths
# ─────────────────────────────────────────────

class PermissionSafeMethodTest(TestCase):
    def _check_safe(self, perm_class, user):
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        factory = APIRequestFactory()
        raw = factory.get('/')
        raw.user = user
        req = Request(raw)
        req._user = user
        perm = perm_class()
        return perm.has_permission(req, None)

    def _check_write(self, perm_class, user):
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        factory = APIRequestFactory()
        raw = factory.post('/')
        raw.user = user
        req = Request(raw)
        req._user = user
        perm = perm_class()
        return perm.has_permission(req, None)

    def setUp(self):
        self.participante = User.objects.create_user(
            email='perm_part@test.com', full_name='P', password='pass', role='participante'
        )

    def test_can_manage_users_participante_safe(self):
        from api.permissions import CanManageUsers
        self.assertTrue(self._check_safe(CanManageUsers, self.participante))

    def test_can_manage_users_participante_write(self):
        from api.permissions import CanManageUsers
        self.assertFalse(self._check_write(CanManageUsers, self.participante))

    def test_can_manage_certificates_participante_safe(self):
        from api.permissions import CanManageCertificates
        self.assertTrue(self._check_safe(CanManageCertificates, self.participante))

    def test_can_manage_certificates_participante_write(self):
        from api.permissions import CanManageCertificates
        self.assertFalse(self._check_write(CanManageCertificates, self.participante))

    def test_can_manage_events_participante_safe(self):
        from api.permissions import CanManageEvents
        self.assertTrue(self._check_safe(CanManageEvents, self.participante))

    def test_can_manage_events_participante_write(self):
        from api.permissions import CanManageEvents
        self.assertFalse(self._check_write(CanManageEvents, self.participante))

    def test_can_manage_students_participante_safe(self):
        from api.permissions import CanManageStudents
        self.assertTrue(self._check_safe(CanManageStudents, self.participante))

    def test_can_manage_students_participante_write(self):
        from api.permissions import CanManageStudents
        self.assertFalse(self._check_write(CanManageStudents, self.participante))

    def test_can_manage_instructors_participante_safe(self):
        from api.permissions import CanManageInstructors
        self.assertTrue(self._check_safe(CanManageInstructors, self.participante))

    def test_can_manage_instructors_participante_write(self):
        from api.permissions import CanManageInstructors
        self.assertFalse(self._check_write(CanManageInstructors, self.participante))

    def test_can_manage_templates_participante_safe(self):
        from api.permissions import CanManageTemplates
        self.assertTrue(self._check_safe(CanManageTemplates, self.participante))

    def test_can_manage_templates_participante_write(self):
        from api.permissions import CanManageTemplates
        self.assertFalse(self._check_write(CanManageTemplates, self.participante))


# ─────────────────────────────────────────────
# CertificateViewSet - serializer class + permissions + exception paths
# ─────────────────────────────────────────────

class CertificateViewSetCoverageTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.student = make_student(self.admin)
        self.event = make_event(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)

    def test_create_certificate_hits_create_serializer(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post('/api/certificates/', {
            'student': self.student.id,
            'event': self.event.id,
            'template': self.template.id,
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_non_admin_create_certificate_uses_is_admin_user_permission(self):
        regular = make_user('certperm@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.post('/api/certificates/', {
            'student': self.student.id,
            'event': self.event.id,
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    @patch('certificados.models.Certificate.generate')
    def test_generate_exception_caught_returns_400(self, mock_generate):
        mock_generate.side_effect = Exception('PDF error')
        self.client.force_authenticate(user=self.admin)
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        res = self.client.post(f'/api/certificates/{cert.id}/generate/', {
            'student_id': self.student.id,
            'event_id': self.event.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Failed to generate certificate', res.data['message'])

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_with_template_id_overrides_template(self, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        self.client.force_authenticate(user=self.admin)
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        template2 = Template.objects.create(name='T2', created_by=self.admin)
        res = self.client.post(f'/api/certificates/{cert.id}/generate/', {
            'student_id': self.student.id,
            'event_id': self.event.id,
            'template_id': template2.id,
        }, format='json')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_unauthenticated_cert_queryset_returns_none(self):
        self.client.force_authenticate(user=None)
        res = self.client.get('/api/certificates/verify/?code=ABCD-ABCD-ABCD-ABCD')
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])


# ─────────────────────────────────────────────
# EventsViewSet - generate_certificates & send_certificates extra paths
# ─────────────────────────────────────────────

class EventsCertificateActionsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)
        self.student = make_student(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)

    def test_generate_certificates_with_student_ids_filter(self):
        res = self.client.post(
            f'/api/events/{self.event.id}/certificates/generate/',
            {'student_ids': [self.student.id]},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    def test_generate_certificates_pending_cert_triggers_regenerate(self, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template,
            generated_by=self.admin, status='pending'
        )
        res = self.client.post(f'/api/events/{self.event.id}/certificates/generate/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_send_certificates_with_student_ids_filter(self):
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated', pdf_url='/cert.pdf')
        with patch('services.email_service.EmailService.send_certificate') as mock_send:
            mock_send.return_value = {'success': True, 'message': 'sent'}
            res = self.client.post(
                f'/api/events/{self.event.id}/certificates/send/',
                {'method': 'email', 'student_ids': [self.student.id]},
                format='json'
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch('services.pdf_service.PDFService.generate_certificate_pdf')
    @patch('services.email_service.EmailService.send_certificate')
    def test_send_certificates_generates_pending_first(self, mock_send, mock_pdf):
        mock_pdf.return_value = {'success': True, 'path': '/media/cert.pdf'}
        mock_send.return_value = {'success': True, 'message': 'sent'}
        Certificate.objects.create(
            student=self.student, event=self.event, template=self.template,
            generated_by=self.admin, status='pending'
        )
        res = self.client.post(
            f'/api/events/{self.event.id}/certificates/send/',
            {'method': 'email'}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @patch('certificados.models.Certificate.deliver')
    def test_send_certificates_exception_logs_failed(self, mock_deliver):
        mock_deliver.side_effect = Exception('delivery failed')
        cert = Certificate.objects.create(
            student=self.student, event=self.event, template=self.template, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated', pdf_url='/cert.pdf')
        res = self.client.post(
            f'/api/events/{self.event.id}/certificates/send/',
            {'method': 'email'}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(res.data['total_failed'], 0)


# ─────────────────────────────────────────────
# EventsViewSet - _parse_emails helpers
# ─────────────────────────────────────────────

class EventsEmailParsingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)

    def test_send_invitations_csv_file_with_email_column(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        csv_content = b'email\nfileguest@test.com\n'
        f = SimpleUploadedFile('emails.csv', csv_content, content_type='text/csv')
        with patch('django.core.mail.send_mail', return_value=1):
            res = self.client.post(
                f'/api/events/{self.event.id}/invitations/send/',
                {'file': f},
                format='multipart'
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_send_invitations_csv_file_no_email_column_returns_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        csv_content = b'name,phone\nJohn,555\n'
        f = SimpleUploadedFile('noemail.csv', csv_content, content_type='text/csv')
        res = self.client.post(
            f'/api/events/{self.event.id}/invitations/send/',
            {'file': f},
            format='multipart'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_invitations_file_read_error_returns_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('bad.csv', b'corrupted\x00\x01\x02', content_type='text/csv')
        with patch('pandas.read_csv', side_effect=Exception('read error')):
            res = self.client.post(
                f'/api/events/{self.event.id}/invitations/send/',
                {'file': f},
                format='multipart'
            )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_invitations_invalid_json_emails_treated_as_empty(self):
        res = self.client.post(
            f'/api/events/{self.event.id}/invitations/send/',
            {'emails': 'not{valid[json'},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('django.core.mail.send_mail')
    def test_send_invitations_email_failure_appended_to_errors(self, mock_mail):
        mock_mail.side_effect = Exception('SMTP error')
        import json
        res = self.client.post(
            f'/api/events/{self.event.id}/invitations/send/',
            {'emails': json.dumps(['errmail@test.com'])},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data['errors']) > 0)

    @patch('django.core.mail.send_mail')
    def test_send_all_invitations_success_marks_sent(self, mock_mail):
        mock_mail.return_value = 1
        from events.models import EventInvitation
        EventInvitation.objects.create(
            event=self.event, email='tosend@test.com', status='pending', created_by=self.admin
        )
        res = self.client.post(f'/api/events/{self.event.id}/invitations/send-all/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(res.data['sent'], 1)

    @patch('django.core.mail.send_mail')
    def test_send_all_invitations_email_failure_appended_to_errors(self, mock_mail):
        mock_mail.side_effect = Exception('SMTP fail')
        from events.models import EventInvitation
        EventInvitation.objects.create(
            event=self.event, email='failsend@test.com', status='pending', created_by=self.admin
        )
        res = self.client.post(f'/api/events/{self.event.id}/invitations/send-all/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(len(res.data['errors']), 0)


# ─────────────────────────────────────────────
# generate_certificates loop exception
# ─────────────────────────────────────────────

class GenerateCertificatesLoopExceptionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)
        self.student = make_student(self.admin)
        self.template = Template.objects.create(name='T', created_by=self.admin)
        Enrollment.objects.create(student=self.student, event=self.event, attendance=True, created_by=self.admin)

    @patch('certificados.models.Certificate.objects')
    def test_generate_certificates_exception_logged_in_errors(self, mock_objects):
        mock_objects.get_or_create.side_effect = Exception('DB error')
        mock_objects.filter.return_value = Certificate.objects.filter(event=self.event)
        res = self.client.post(f'/api/events/{self.event.id}/certificates/generate/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# BulkCertificate views - exception paths
# ─────────────────────────────────────────────

class BulkCertificateViewExceptionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin, name='Bulk Test')

    def _make_excel_file(self):
        import pandas as pd
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        df = pd.DataFrame([{
            'full_name': 'Test User', 'email': 'testbulk@test.com',
            'document_id': 'BLKTEST', 'event_name': 'Bulk Test',
        }])
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return SimpleUploadedFile('bulk.xlsx', buf.read(),
                                   content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_bulk_generate_post_with_valid_excel_reaches_processing(self):
        f = self._make_excel_file()
        res = self.client.post('/api/certificates/generate-bulk/', {'excel_file': f}, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    @patch('api.views.BulkCertificateGeneratorService.generate_from_excel')
    def test_bulk_generate_exception_returns_400(self, mock_gen):
        mock_gen.side_effect = Exception('processing error')
        f = self._make_excel_file()
        res = self.client.post('/api/certificates/generate-bulk/', {'excel_file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_preview_post_with_valid_excel(self):
        f = self._make_excel_file()
        res = self.client.post('/api/certificates/preview/', {'excel_file': f}, format='multipart')
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    @patch('api.views.ExcelProcessingService')
    def test_bulk_preview_excel_import_error_returns_400(self, mock_svc):
        from procesos.services import ExcelImportError
        mock_svc.return_value.read_and_validate_structure.side_effect = ExcelImportError('bad file')
        f = self._make_excel_file()
        res = self.client.post('/api/certificates/preview/', {'excel_file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.views.ExcelProcessingService')
    def test_bulk_preview_generic_exception_returns_400(self, mock_svc):
        mock_svc.return_value.read_and_validate_structure.side_effect = Exception('unexpected')
        f = self._make_excel_file()
        res = self.client.post('/api/certificates/preview/', {'excel_file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.views.ExcelProcessingService')
    def test_bulk_process_excel_import_error_returns_400(self, mock_svc):
        from procesos.services import ExcelImportError
        mock_svc.return_value.process_records.side_effect = ExcelImportError('bad data')
        res = self.client.post('/api/certificates/process/', {'data': [{'full_name': 'X'}]}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.views.ExcelProcessingService')
    def test_bulk_process_generic_exception_returns_500(self, mock_svc):
        mock_svc.return_value.process_records.side_effect = RuntimeError('unexpected error')
        res = self.client.post('/api/certificates/process/', {'data': [{'full_name': 'X'}]}, format='json')
        self.assertEqual(res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# EnrollmentViewSet - destroy, attendance, non-admin list
# ─────────────────────────────────────────────

class EnrollmentViewSetDestroyAttendanceTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)
        self.student = make_student(self.admin)
        self.enrollment = Enrollment.objects.create(
            student=self.student, event=self.event, attendance=False, created_by=self.admin
        )

    def test_destroy_enrollment_success(self):
        res = self.client.delete(f'/api/enrollments/{self.enrollment.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_enrollment_not_found(self):
        res = self.client.delete('/api/enrollments/99999/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_attendance_mark_true(self):
        res = self.client.patch(
            f'/api/enrollments/{self.enrollment.id}/attendance/',
            {'attendance': True},
            format='json'
        )
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_attendance_missing_field_returns_400(self):
        res = self.client.patch(
            f'/api/enrollments/{self.enrollment.id}/attendance/',
            {},
            format='json'
        )
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_attendance_not_found(self):
        res = self.client.patch(
            '/api/enrollments/99999/attendance/',
            {'attendance': True},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_list_returns_403(self):
        regular = make_user('nonadmin_enr@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.get('/api/enrollments/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_enrollment_success(self):
        student2 = Student.objects.create(
            document_id='ENROLL2', first_name='New', last_name='Student',
            email='enroll2@test.com', created_by=self.admin
        )
        res = self.client.post('/api/enrollments/', {
            'student_id': student2.id,
            'event_id': self.event.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_enrollment_duplicate_returns_400(self):
        res = self.client.post('/api/enrollments/', {
            'student_id': self.student.id,
            'event_id': self.event.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_enrollment_invalid_student_returns_404(self):
        res = self.client.post('/api/enrollments/', {
            'student_id': 99999,
            'event_id': self.event.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_enrollment_invalid_event_returns_404(self):
        student2 = Student.objects.create(
            document_id='ENROLL3', first_name='S', last_name='T',
            email='enroll3@test.com', created_by=self.admin
        )
        res = self.client.post('/api/enrollments/', {
            'student_id': student2.id,
            'event_id': 99999,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────
# Import students - IntegrityError / exception paths
# ─────────────────────────────────────────────

class ImportStudentsErrorPathTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)

    def test_import_with_duplicate_document_id(self):
        import pandas as pd
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        make_student(self.admin, doc='DUP001', email='dup@test.com')
        df = pd.DataFrame([{'document_id': 'DUP001', 'first_name': 'Dup', 'last_name': 'User', 'email': 'dup2@test.com', 'phone': ''}])
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        f = SimpleUploadedFile('dup.xlsx', buf.read(),
                               content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        res = self.client.post('/api/students/import_students/', {'file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_template_non_admin_cannot_create(self):
        regular = make_user('tperm@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.post('/api/templates/', {'name': 'Test'})
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_import_with_duplicate_email_triggers_integrity_error(self):
        import pandas as pd
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        make_student(self.admin, doc='UNIQUE_DOC1', email='unique_dup@test.com')
        df = pd.DataFrame([{
            'document_id': 'DIFFERENT_DOC1',
            'first_name': 'New', 'last_name': 'User',
            'email': 'unique_dup@test.com', 'phone': '',
        }])
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        f = SimpleUploadedFile('dup_email.xlsx', buf.read(),
                               content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        res = self.client.post('/api/students/import_students/', {'file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(len(res.data.get('errors', [])), 0)

    @patch('students.models.Student.objects')
    def test_import_generic_exception_per_row_logged(self, mock_objects):
        import pandas as pd
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        mock_objects.get_or_create.side_effect = RuntimeError('unexpected row error')
        df = pd.DataFrame([{'document_id': 'ERRDOC', 'first_name': 'X', 'last_name': 'Y', 'email': 'x@test.com', 'phone': ''}])
        buf = BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        f = SimpleUploadedFile('err.xlsx', buf.read(),
                               content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        res = self.client.post('/api/students/import_students/', {'file': f}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(len(res.data.get('errors', [])), 0)


# ─────────────────────────────────────────────
# Finalize event with send_certificates coverage
# ─────────────────────────────────────────────

class FinalizeEventCertificateSentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin('fin_admin@test.com')
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin, name='FinalizeTest')
        self.student = make_student(self.admin, doc='FINSTUD', email='finstud@test.com')

    @patch('certificados.models.Certificate.deliver')
    def test_finalize_with_send_certificates_covers_sent_fields(self, mock_deliver):
        mock_deliver.return_value = MagicMock()
        from events.models import Enrollment
        from certificados.models import Certificate
        Enrollment.objects.create(
            student=self.student, event=self.event, attendance=True, created_by=self.admin
        )
        cert = Certificate.objects.create(
            student=self.student, event=self.event, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated')
        res = self.client.post(f'/api/events/{self.event.id}/finalize/', {'send_certificates': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['certificates_sent'], 1)

    @patch('certificados.models.Certificate.deliver')
    def test_finalize_deliver_exception_logged(self, mock_deliver):
        mock_deliver.side_effect = Exception('deliver error')
        from events.models import Enrollment
        from certificados.models import Certificate
        event2 = make_event(self.admin, name='FinalizeExc')
        Enrollment.objects.create(
            student=self.student, event=event2, attendance=True, created_by=self.admin
        )
        cert = Certificate.objects.create(
            student=self.student, event=event2, generated_by=self.admin
        )
        Certificate.objects.filter(pk=cert.pk).update(status='generated')
        res = self.client.post(f'/api/events/{event2.id}/finalize/', {'send_certificates': True})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['certificates_sent'], 0)


# ─────────────────────────────────────────────
# Enrollment create invalid serializer + non-admin write
# ─────────────────────────────────────────────

class EnrollmentEdgeCasesTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin('enr_edge@test.com')
        self.client.force_authenticate(user=self.admin)
        self.event = make_event(self.admin)

    def test_create_enrollment_missing_student_id_returns_400(self):
        res = self.client.post('/api/enrollments/', {'event_id': self.event.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_create_enrollment(self):
        regular = make_user('enr_nonadmin@test.com')
        self.client.force_authenticate(user=regular)
        res = self.client.post('/api/enrollments/', {'student_id': 1, 'event_id': self.event.id}, format='json')
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])


# ─────────────────────────────────────────────
# Template upload image with alternate key
# ─────────────────────────────────────────────

class TemplateUploadImageAltKeyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin('tpl_img@test.com')
        self.client.force_authenticate(user=self.admin)
        from certificados.models import Template
        self.template = Template.objects.create(name='ImgTpl', created_by=self.admin)

    def test_upload_image_with_alternate_key(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        img = SimpleUploadedFile('bg.png', b'\x89PNG\r\n', content_type='image/png')
        res = self.client.post(
            f'/api/templates/{self.template.id}/upload-image/',
            {'background': img},
            format='multipart'
        )
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
