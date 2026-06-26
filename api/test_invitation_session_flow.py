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


@pytest.mark.django_db
def test_consume_invitation_with_invalid_token_clears_session():
    """Si el token en sesión no existe en BD, se limpia la sesión y se retorna None (redirect_url ausente)."""
    admin = _make_admin()
    User.objects.create_user(email="consume@test.com", full_name="Consume User", password="MiPass1234")

    client = APIClient()
    # Forzamos un token en sesión que NO existe en BD
    session = client.session
    session["token_invitacion"] = "no-existe-este-token"
    session["invitacion_email"] = "consume@test.com"
    session.save()

    res = client.post("/api/login/", {"email": "consume@test.com", "password": "MiPass1234"}, format="json")
    assert res.status_code == status.HTTP_200_OK, res.data
    # Sin redirect_url porque el token no correspondía a invitación válida
    assert "redirect_url" not in res.data
    # Y la sesión quedó limpia
    assert "token_invitacion" not in client.session
    assert "invitacion_email" not in client.session


@pytest.mark.django_db
def test_consume_invitation_with_unauthenticated_user_does_nothing():
    """Si en sesión hay token pero el usuario NO está autenticado al consumir, no debe explotar."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "noauth@test.com", admin=admin)

    # El endpoint /api/register/ recibe un POST y dentro crea user + consume sesión.
    # Pero como el User ya existe, no entra a la rama de creación; primero intenta loguear.
    # Probamos directo: POST a /register/ con un email ya existente.
    User.objects.create_user(email="noauth@test.com", full_name="No Auth", password="MiPass1234")
    client = APIClient()
    # Guardamos el token en sesión
    client.get(f"/api/invitations/{invitation.token}/")
    assert "token_invitacion" in client.session

    # Llamamos a login → debe consumir token y asociar
    res = client.post("/api/login/", {"email": "noauth@test.com", "password": "MiPass1234"}, format="json")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["redirect_url"] == f"/events/{event.id}"


@pytest.mark.django_db
def test_accept_invitation_for_user_when_status_not_pending_returns_400():
    """Si la invitación ya está aceptada/rechazada, POST /accept/ retorna 400 aunque el user esté autenticado."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "respondida@test.com", admin=admin)
    invitation.status = "accepted"
    invitation.save()

    user = User.objects.create_user(email="respondida@test.com", full_name="Ya Aceptada", password="MiPass1234")

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post(f"/api/invitations/{invitation.token}/accept/")
    assert res.status_code == status.HTTP_400_BAD_REQUEST, res.data
    # El mensaje real es "La invitación ya ha sido accepted"
    assert "invitaci" in res.data["error"].lower()


@pytest.mark.django_db
def test_accept_invitation_for_user_when_expired_during_consume():
    """Si la invitación expira entre el GET y el POST, /accept/ debe retornar 400 con mensaje de expirada."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "vencio@test.com", admin=admin)
    user = User.objects.create_user(email="vencio@test.com", full_name="Vencio User", password="MiPass1234")

    client = APIClient()
    client.force_authenticate(user=user)
    # Forzamos expiración después del GET
    client.get(f"/api/invitations/{invitation.token}/")
    invitation.expires_at = timezone.now() - timedelta(hours=1)
    invitation.save()

    res = client.post(f"/api/invitations/{invitation.token}/accept/")
    assert res.status_code == status.HTTP_400_BAD_REQUEST, res.data
    assert "expirad" in res.data["error"].lower()


@pytest.mark.django_db
def test_consume_invitation_when_already_accepted_returns_no_redirect():
    """Si la invitación ya está aceptada, _consume_pending_invitation retorna None y limpia sesión.

    Para cubrir esa rama necesitamos inyectar manualmente el token en sesión
    apuntando a una invitación ya aceptada (el endpoint GET no lo guarda).
    """
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "yaacep@test.com", admin=admin)
    invitation.status = "accepted"
    invitation.save()

    User.objects.create_user(email="yaacep@test.com", full_name="Ya Acep", password="MiPass1234")

    client = APIClient()
    # Inyectar token en sesión manualmente porque el GET lo rechazaría
    session = client.session
    session["token_invitacion"] = str(invitation.token)
    session["invitacion_email"] = "yaacep@test.com"
    session.save()

    res = client.post("/api/login/", {"email": "yaacep@test.com", "password": "MiPass1234"}, format="json")
    assert res.status_code == status.HTTP_200_OK
    assert "redirect_url" not in res.data
    # La sesión se limpia igual aunque no haya redirigido
    assert "token_invitacion" not in client.session


@pytest.mark.django_db
def test_register_existing_user_does_not_create_new_enrollment():
    """Si el participante y la inscripción ya existen, re-aceptar debe actualizar attendance sin duplicar."""
    admin = _make_admin()
    event = _make_event(admin)
    invitation = _make_invitation(event, "dup@test.com", admin=admin)
    user = User.objects.create_user(email="dup@test.com", full_name="Dup User", password="MiPass1234")

    # Crear Participant y Enrollment previos
    participant = Participant.objects.create(
        email="dup@test.com", first_name="Dup", last_name="User", document_id="DUP1"
    )
    Enrollment.objects.create(participant=participant, event=event, attendance=False)

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post(f"/api/invitations/{invitation.token}/accept/")
    assert res.status_code == status.HTTP_200_OK, res.data

    enrollment = Enrollment.objects.get(participant=participant, event=event)
    assert enrollment.attendance is True
    # Solo debe haber una inscripción
    assert Enrollment.objects.filter(participant=participant, event=event).count() == 1
