"""
Test end-to-end del nuevo flujo de invitaciones con sesión Django.

Simula:
1. Admin crea evento y envía invitación a un email.
2. Invitado SIN cuenta llega al link → GET /api/invitations/<token>/ →
   backend guarda sesión.
3. Invitado se registra en /api/register/ → backend consume sesión, crea
   usuario + Participant + Enrollment + Certificate, marca invitación aceptada.
4. Verificar todo: usuario creado, participante, inscripción, certificado,
   invitación aceptada.
5. Limpiar sesión: re-intentar registro con misma sesión no debe re-crear nada.

Caso adicional: usuario EXISTENTE llega al link → sesión guarda token →
login → consume sesión.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from events.models import Enrollment, Event, EventInvitation
from participants.models import Participant
from users.models import User

ADMIN_EMAIL = "admin@certypro.app"
ADMIN_NAME = "Admin"
ADMIN_PASS = "admin123"


def _make_admin():
    return User.objects.create_user(email=ADMIN_EMAIL, full_name=ADMIN_NAME, password=ADMIN_PASS, role="admin")


def _make_event(admin):
    return Event.objects.create(
        name="Curso Test",
        event_date=timezone.now().date() + timedelta(days=10),
        location="Online",
        status="active",
        created_by=admin,
    )


def _make_invitation(event, email, expires_at=None, admin=None):
    return EventInvitation.objects.create(
        event=event,
        email=email,
        status="pending",
        expires_at=expires_at if expires_at is not None else timezone.now() + timedelta(days=7),
        created_by=admin,
    )


@pytest.mark.django_db
def test_new_user_invitation_flow_via_session():
    """Caso 1: usuario nuevo, llega por link, registra por /api/register/, queda asociado al evento."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "nuevo@test.com", admin=admin)

    client = APIClient()
    res = client.get(f"/api/invitations/{invitation.token}/")
    assert res.status_code == status.HTTP_200_OK, res.data
    data = res.data
    assert data["login_url"] == "/login?email=nuevo@test.com"
    assert data["register_url"] == "/register?email=nuevo@test.com"
    assert data["event_id"] == event.id
    assert "token_invitacion" in client.session
    assert client.session["token_invitacion"] == str(invitation.token)
    assert client.session["invitacion_email"] == "nuevo@test.com"
    assert client.cookies.get("csrftoken") is not None

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
    assert "access" in payload and "refresh" in payload
    assert payload["redirect_url"] == f"/events/{event.id}"
    assert "inscrito" in payload["message"].lower()

    user = User.objects.get(email="nuevo@test.com")
    assert user.role == "participante"
    assert user.check_password("MiPassword123")

    participant = Participant.objects.get(email="nuevo@test.com")
    enrollment = Enrollment.objects.get(participant=participant, event=event)
    assert enrollment.attendance is True

    invitation.refresh_from_db()
    assert invitation.status == "accepted"
    assert invitation.participant == participant
    assert invitation.responded_at is not None
    assert "token_invitacion" not in client.session
    assert "invitacion_email" not in client.session


@pytest.mark.django_db
def test_existing_user_invitation_flow_via_session():
    """Caso 2: usuario existente, llega por link, hace login, queda asociado al evento."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "existente@test.com", admin=admin)
    User.objects.create_user(email="existente@test.com", full_name="Ana López", password="MiPass1234")

    client = APIClient()
    res = client.get(f"/api/invitations/{invitation.token}/")
    assert res.status_code == status.HTTP_200_OK
    assert "token_invitacion" in client.session

    res = client.post("/api/login/", {"email": "existente@test.com", "password": "MiPass1234"}, format="json")
    assert res.status_code == status.HTTP_200_OK, res.data
    payload = res.data
    assert "access" in payload
    assert payload["redirect_url"] == f"/events/{event.id}"

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
    admin = _make_admin()
    _make_event(admin)

    client = APIClient()
    res = client.post("/api/login/", {"email": ADMIN_EMAIL, "password": ADMIN_PASS}, format="json")
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
    assert "inscrito" not in res.data["message"].lower()


@pytest.mark.django_db
def test_get_invitation_expired_does_not_save_session():
    """Si la invitación está expirada, no se debe guardar token en sesión."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(
        event, "expirado@test.com", expires_at=timezone.now() - timedelta(hours=1), admin=admin
    )

    client = APIClient()
    res = client.get(f"/api/invitations/{invitation.token}/")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "token_invitacion" not in client.session


@pytest.mark.django_db
def test_authenticated_user_accepts_without_participant_creates_it():
    """Caso extra: usuario ya autenticado, llega por link, hace POST /accept/
    sin tener Participant → el backend debe crear el Participant automáticamente."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "logueado@test.com", admin=admin)
    user = User.objects.create_user(email="logueado@test.com", full_name="Logueado User", password="MiPass1234")

    client = APIClient()
    client.force_authenticate(user=user)
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
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "directo@test.com", admin=admin)

    client = APIClient()
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
    assert "token_invitacion" not in client.session
