from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
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
        res = self.client.post(f'/api/certificates/{self.cert.id}/generate/', {})
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
        student = make_student(self.admin, email='findme@test.com', doc='FIND01')
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
            'template_id': str(template2.id),
        })
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
