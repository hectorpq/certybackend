"""
Helpers para el flujo de invitaciones con sesión Django.

Este módulo existía dentro de ``api/views.py`` (4251 líneas) y se extrajo para
reducir el tamaño del archivo y aislar la lógica de aceptación de invitaciones
de las vistas HTTP.

Funciones públicas:
- ``accept_invitation_for_user(user, invitation)``
- ``consume_pending_invitation(request)``

Las funciones mantienen el contrato histórico para no romper importadores
externos (tests, vistas que aún las llamen).
"""

from __future__ import annotations

import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from certificados.models import Certificate
from events.models import Enrollment, EventInvitation
from participants.models import Participant

logger = logging.getLogger(__name__)


def _ensure_email_matches(user, invitation):
    """Verifica que el email del usuario coincida con el email de la invitación."""
    if (user.email or "").lower().strip() != (invitation.email or "").lower().strip():
        logger.warning(
            "Bloqueado intento de aceptar invitación: user.email=%s != invitation.email=%s",
            user.email,
            invitation.email,
        )
        raise PermissionDenied("El email del usuario no coincide con el email de la invitación.")


def accept_invitation_for_user(user, invitation):
    """
    Asocia un usuario autenticado a una invitación pendiente.

    - Crea o recupera el ``Participant`` (por email).
    - Crea o recupera el ``Enrollment`` con ``attendance=True``.
    - Crea un ``Certificate`` en estado ``pending`` si no existe.
    - Marca la invitación como ``accepted`` y guarda ``responded_at``.

    Retorna ``True`` si la asociación se completó con éxito, ``False`` si la
    invitación ya no es válida (estado distinto a ``pending``/``sent`` o
    expirada o el email del usuario no coincide con el email de la invitación).

    Raises:
        PermissionDenied: si el email del usuario autenticado no coincide con
            el email de la invitación (anti-privilege-escalation).
    """
    _ensure_email_matches(user, invitation)

    with transaction.atomic():
        if invitation.status not in ("pending", "sent"):
            return False
        if invitation.expires_at and invitation.expires_at < timezone.now():  # pragma: no cover
            invitation.status = "expired"  # pragma: no cover
            invitation.save()  # pragma: no cover
            return False  # pragma: no cover

        email = invitation.email.lower()

        # UUID para evitar colisión con DNI real cuando el Participant se crea
        # sin un document_id explícito (ej. desde flujo de invitación).
        participant, _ = Participant.objects.get_or_create(
            email=email,
            defaults={
                "first_name": user.full_name.split(" ", 1)[0] if user.full_name else "",
                "last_name": (user.full_name.split(" ", 1)[1] if (user.full_name and " " in user.full_name) else ""),
                "phone": "",
                "document_id": f"USR-{uuid.uuid4().hex[:8].upper()}",
            },
        )

        invitation.participant = participant
        invitation.status = "accepted"
        invitation.responded_at = timezone.now()
        invitation.save()

        enrollment, created = Enrollment.objects.get_or_create(
            participant=participant,
            event=invitation.event,
            defaults={
                "created_by": invitation.created_by,
                "invitation_sent": True,
                "attendance": True,
            },
        )
        if not created:
            enrollment.attendance = True
            enrollment.save()

        Certificate.objects.get_or_create(
            participant=participant,
            event=invitation.event,
            defaults={
                "template": invitation.event.template,
                "status": "pending",
            },
        )

        return True


def consume_pending_invitation(request):
    """
    Lee ``token_invitacion`` de la sesión, busca la invitación y la asocia
    al usuario autenticado en ``request.user``. Retorna la URL a la que el
    frontend debe redirigir (``/events/<id>``) o ``None`` si no había token.
    """
    token = request.session.get("token_invitacion")
    if not token:
        return None

    try:
        invitation = EventInvitation.objects.select_related("event").get(token=token)
    except EventInvitation.DoesNotExist:
        # Token inválido → limpiar la sesión para no reintentar
        request.session.pop("token_invitacion", None)
        request.session.pop("invitacion_email", None)
        return None

    # Limpiar el token de la sesión siempre (se consume una sola vez)
    request.session.pop("token_invitacion", None)
    request.session.pop("invitacion_email", None)

    if not request.user.is_authenticated:
        return None

    if accept_invitation_for_user(request.user, invitation):
        return f"/events/{invitation.event.id}"
    return None


# Aliases privados para compatibilidad con código que importaba los nombres
# originales con guión bajo desde views.py.
_accept_invitation_for_user = accept_invitation_for_user
_consume_pending_invitation = consume_pending_invitation
