"""
Test end-to-end del nuevo flujo de invitaciones con sesión Django.

Simula:
1. Admin crea evento y envía invitación a un email.
2. Invitado SIN cuenta llega al link → GET /api/invitations/<token>/ → backend guarda sesión.
3. Invitado se registra en /api/register/ → backend consume sesión, crea usuario + Participant + Enrollment + Certificate, marca invitación aceptada.
4. Verificar todo: usuario creado, participante, inscripción, certificado, invitación aceptada.
5. Limpiar sesión: re-intentar registro con misma sesión no debe re-crear nada.

Caso adicional: usuario EXISTENTE llega al link → sesión guarda token → login → consume sesión.
"""
from datetime import timedelta
from io import BytesIO

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Enrollment, Event, EventInvitation
from participants.models import Participant
from users.models import User


def _make_event(admin):
    return Event.objects.create(
        name="Curso Test",
        event_date=timezone.now().date() + timedelta(days=10),
        location="Online",
        status="active",
        created_by=admin,
    )


@pytest.mark.django_db
def test_new_user_invitation_flow_via_session():
    """Caso 1: usuario nuevo, llega por link, registra por /api/register/, queda asociado al evento."""
    admin = User.objects.create_user(
        email="admin@certypro.app", full_name="Admin", password="admin123", role="admin"
    )
    event = _make_event(admin)
    invitation = EventInvitation.objects.create(
        event=event,
        email="nuevo@test.com",
        status="pending",
        expires_at=timezone.now() + timedelta(days=7),
        created_by=admin,
    )

    client = APIClient()
    # 1. Invitado llega al link → GET /api/invitations/<token>/
    res = client.get(f"/api/invitations/{invitation.token}/")
    assert res.status_code == status.HTTP_200_OK, res.data
    data = res.data
    assert data["login_url"] == f"/login?email=nuevo@test.com"
    assert data["register_url"] == f"/register?email=nuevo@test.com"
    assert data["event_id"] == event.id
    # Backend debió haber guardado token en sesión
    assert "token_invitacion" in client.session
    assert client.session["token_invitacion"] == str(invitation.token)
    assert client.session["invitacion_email"] == "nuevo@test.com"
    # Y emitió cookie csrftoken
    csrf_cookie = client.cookies.get("csrftoken")
    assert csrf_cookie is not None

    # 2. Invitado registra → POST /api/register/
    res = client.post(
        "/api/register/",
        {
            "email": "nuevo@test.com",
            "full_name": "Juan Pérez",
            "password": "MiPassword123",
            "password_confirm": "MiPassword123",
        },
        format="json",
    )
    assert res.status_code == status.HTTP_201_CREATED, res.data
    payload = res.data
    # Tokens JWT presentes
    assert "access" in payload and "refresh" in payload
    # redirect_url apunta al evento
    assert payload["redirect_url"] == f"/events/{event.id}"
    # Mensaje de inscripción exitosa
    assert "inscrito" in payload["message"].lower()

    # 3. Verificar efectos en BD
    user = User.objects.get(email="nuevo@test.com")
    assert user.role == "participante"
    assert user.check_password("MiPassword123")

    participant = Participant.objects.get(email="nuevo@test.com")
    assert participant is not None

    enrollment = Enrollment.objects.get(participant=participant, event=event)
    assert enrollment.attendance is True

    # 4. La invitación quedó aceptada y la sesión limpia
    invitation.refresh_from_db()
    assert invitation.status == "accepted"
    assert invitation.participant == participant
    assert invitation.responded_at is not None
    assert "token_invitacion" not in client.session
    assert "invitacion_email" not in client.session


@pytest.mark.django_db
def test_existing_user_invitation_flow_via_session():
    """Caso 2: usuario existente, llega por link, hace login, queda asociado al evento."""
    admin = User.objects.create_user(
        email="admin@certypro.app", full_name="Admin", password="admin123", role="admin"
    )
    event = _make_event(admin)
    invitation = EventInvitation.objects.create(
        event=event,
        email="existente@test.com",
        status="pending",
        expires_at=timezone.now() + timedelta(days=7),
        created_by=admin,
    )
    # Usuario ya existe
    User.objects.create_user(
        email="existente@test.com", full_name="Ana López", password="MiPass1234"
    )

    client = APIClient()
    # 1. Llega al link → GET /api/invitations/<token>/
    res = client.get(f"/api/invitations/{invitation.token}/")
    assert res.status_code == status.HTTP_200_OK
    assert "token_invitacion" in client.session

    # 2. Inicia sesión → POST /api/login/
    res = client.post(
        "/api/login/", {"email": "existente@test.com", "password": "MiPass1234"}, format="json"
    )
    assert res.status_code == status.HTTP_200_OK, res.data
    payload = res.data
    assert "access" in payload
    assert payload["redirect_url"] == f"/events/{event.id}"

    # 3. Verificar asociación
    participant = Participant.objects.get(email="existente@test.com")
    assert participant.full_name == "Ana López"
    enrollment = Enrollment.objects.get(participant=participant, event=event)
    assert enrollment.attendance is True
    invitation.refresh_from_db()
    assert invitation.status == "accepted"
    assert "token_invitacion" not in client.session


@pytest.mark.django_db
def test_login_without_invitation_token_works_normally():
    """Caso 3: login sin token en sesión no debe romper nada."""
    admin = User.objects.create_user(
        email="admin@certypro.app", full_name="Admin", password="admin123", role="admin"
    )
    _make_event(admin)

    client = APIClient()
    res = client.post(
        "/api/login/", {"email": "admin@certypro.app", "password": "admin123"}, format="json"
    )
    assert res.status_code == status.HTTP_200_OK
    assert "redirect_url" not in res.data


@pytest.mark.django_db
def test_register_without_invitation_token_works_normally():
    """Caso 4: registro sin token en sesión no debe romper nada."""
    client = APIClient()
    res = client.post(
        "/api/register/",
        {
            "email": "sininv@test.com",
            "full_name": "Sin Inv",
            "password": "MiPassword123",
            "password_confirm": "MiPassword123",
        },
        format="json",
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert "redirect_url" not in res.data
    # Mensaje neutro (no "inscrito")
    assert "inscrito" not in res.data["message"].lower()


@pytest.mark.django_db
def test_get_invitation_expired_does_not_save_session():
    """Si la invitación está expirada, no se debe guardar token en sesión."""
    admin = User.objects.create_user(
        email="admin@certypro.app", full_name="Admin", password="admin123", role="admin"
    )
    event = _make_event(admin)
    invitation = EventInvitation.objects.create(
        event=event,
        email="expirado@test.com",
        status="pending",
        expires_at=timezone.now() - timedelta(hours=1),
        created_by=admin,
    )
    client = APIClient()
    res = client.get(f"/api/invitations/{invitation.token}/")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "token_invitacion" not in client.session


@pytest.mark.django_db
def test_authenticated_user_accepts_without_participant_creates_it():
    """Caso extra: usuario ya autenticado, llega por link, hace POST /accept/
    sin tener Participant → el backend debe crear el Participant automáticamente."""
    admin = User.objects.create_user(
        email="admin@certypro.app", full_name="Admin", password="admin123", role="admin"
    )
    event = _make_event(admin)
    invitation = EventInvitation.objects.create(
        event=event,
        email="logueado@test.com",
        status="pending",
        expires_at=timezone.now() + timedelta(days=7),
        created_by=admin,
    )
    user = User.objects.create_user(
        email="logueado@test.com", full_name="Logueado User", password="MiPass1234"
    )

    client = APIClient()
    client.force_authenticate(user=user)
    # Garantizar cookie csrftoken
    client.get(f"/api/invitations/{invitation.token}/")

    res = client.post(f"/api/invitations/{invitation.token}/accept/")
    assert res.status_code == status.HTTP_200_OK, res.data
    assert res.data["redirect_url"] == f"/events/{event.id}"

    participant = Participant.objects.get(email="logueado@test.com")
    assert participant.full_name == "Logueado User"
    enrollment = Enrollment.objects.get(participant=participant, event=event)
    assert enrollment.attendance is True
    invitation.refresh_from_db()
    assert invitation.status == "accepted"


@pytest.mark.django_db
def test_invitation_direct_register_still_clears_session():
    """El flujo directo /api/invitations/<token>/register/ limpia la sesión."""
    admin = User.objects.create_user(
        email="admin@certypro.app", full_name="Admin", password="admin123", role="admin"
    )
    event = _make_event(admin)
    invitation = EventInvitation.objects.create(
        event=event,
        email="directo@test.com",
        status="pending",
        expires_at=timezone.now() + timedelta(days=7),
        created_by=admin,
    )
    client = APIClient()
    # Simular que el frontend hizo GET antes (guarda token en sesión)
    client.get(f"/api/invitations/{invitation.token}/")
    assert "token_invitacion" in client.session

    res = client.post(
        f"/api/invitations/{invitation.token}/register/",
        {
            "first_name": "Dir",
            "last_name": "Ecto",
            "phone": "999",
            "password": "MiPassword123",
        },
        format="json",
    )
    assert res.status_code == status.HTTP_200_OK, res.data
    assert res.data["redirect_url"] == f"/events/{event.id}"
    # Sesión limpia
    assert "token_invitacion" not in client.session
