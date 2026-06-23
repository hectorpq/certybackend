"""
ViewSets (views) for Certificate and Delivery APIs
"""

import json
import logging
from io import BytesIO

from django.db import models, transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.audit import get_client_ip, log_action
from api.models import AuditLog
from api.permissions import is_admin, is_operational_user
from certificados.models import Certificate, Template
from deliveries.models import DeliveryLog
from events.models import Event
from instructors.models import Instructor
from participants.models import Participant
from procesos.services import BulkCertificateGeneratorService, ExcelImportError, ExcelProcessingService  # noqa: F401
from users.models import User

from .serializers import (
    AuditLogSerializer,
    BulkProcessDataSerializer,
    CertificateCreateSerializer,
    CertificateDeliverSerializer,
    CertificateDetailSerializer,
    CertificateGenerateSerializer,
    CertificateListSerializer,
    CertificateRetrySerializer,
    ChangelogSerializer,
    DeliveryLogSerializer,
    EnrollmentCreateSerializer,
    EnrollmentSerializer,
    EventEnrollSerializer,
    EventFinalizeSerializer,
    EventGenerateCertificatesSerializer,
    EventInvitationSerializer,
    EventSendCertificatesSerializer,
    EventSendInvitationsSerializer,
    EventSerializer,
    ExcelBulkImportSerializer,
    InstructorSerializer,
    InvitationDetailSerializer,
    InvitationRegisterSerializer,
    ParticipantSerializer,
    TemplateCreateSerializer,
    TemplateSerializer,
    TemplateUpdateSerializer,
    UserAuthSerializer,
    UserRegisterSerializer,
)

logger = logging.getLogger(__name__)


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone, write access to admin only
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsCertificateOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access if user is the owner (student) or admin
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class RegisterView(APIView):
    """
    API endpoint para registro de nuevos usuarios

    POST /api/register/
    Body: {
        "email": "user@example.com",
        "full_name": "Juan Pérez",
        "password": "secure_password_123",
        "password_confirm": "secure_password_123"
    }

    Response (201 Created):
    {
        "id": 1,
        "email": "user@example.com",
        "full_name": "Juan Pérez",
        "message": "Cuenta creada exitosamente"
    }
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Autenticación"],
        summary="Registrar nuevo usuario",
        description=(
            "Crea una nueva cuenta de usuario en el sistema. **No requiere autenticación previa.**\n\n"
            "Valida que las contraseñas coincidan y que el email no esté ya registrado. "
            "Devuelve el `id`, `email`, `full_name` del usuario creado y un mensaje de confirmación."
        ),
        request=UserRegisterSerializer,
        examples=[
            OpenApiExample(
                "Registro exitoso",
                value={
                    "email": "nuevo@example.com",
                    "full_name": "Juan Pérez",
                    "password": "MiPassword123",
                    "password_confirm": "MiPassword123",
                },
                request_only=True,
            ),
        ],
        responses={
            201: OpenApiResponse(description="Usuario creado exitosamente. Retorna id, email, full_name y mensaje."),
            400: OpenApiResponse(
                description="Datos inválidos: email duplicado, contraseñas no coinciden o campos requeridos faltantes."
            ),
        },
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "message": "Cuenta creada exitosamente. Por favor inicia sesión.",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint para login de usuarios

    POST /api/login/
    Body: {
        "email": "user@example.com",
        "password": "secure_password_123"
    }

    Response (200 OK):
    {
        "access": "eyJ...",
        "refresh": "eyJ...",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "first_name": "Juan",
            "email": "user@example.com"
        }
    }
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Autenticación"],
        summary="Iniciar sesión",
        description=(
            "Autentica al usuario con email y contraseña. **No requiere autenticación previa.**\n\n"
            "Si las credenciales son válidas retorna un par de tokens JWT:\n"
            "- `access`: token de corta duración para autenticar cada petición "
            "(enviar en header `Authorization: Bearer <access>`).\n"
            "- `refresh`: token de larga duración para obtener un nuevo `access` sin volver a loguearse.\n\n"
            "También retorna los datos básicos del usuario: id, email, nombre completo, rol e is_staff."
        ),
        request=UserAuthSerializer,
        examples=[
            OpenApiExample(
                "Login exitoso",
                value={"email": "admin@example.com", "password": "MiPassword123"},
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Login exitoso. Retorna access token, refresh token y datos del usuario."),
            400: OpenApiResponse(description="Credenciales inválidas o usuario inactivo."),
        },
    )
    def post(self, request):
        serializer = UserAuthSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            logger.info("LOGIN_SUCCESS email=%s ip=%s", user.email, self._get_client_ip(request))
            log_action("user_login", user=user, ip_address=get_client_ip(request))
            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "is_staff": user.is_staff,
                    },
                },
                status=status.HTTP_200_OK,
            )

        attempted_email = request.data.get("email", "")
        logger.warning(
            "LOGIN_FAILED email=%s ip=%s errors=%s",
            attempted_email,
            self._get_client_ip(request),
            serializer.errors,
        )
        log_action(
            "user_login_failed",
            ip_address=get_client_ip(request),
            email=attempted_email,
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _get_client_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")


class GoogleAuthView(APIView):
    """
    API endpoint para autenticación con Google OAuth

    POST /api/auth/google/
    Body: {
        "token": "google_id_token"
    }

    Response (200 OK):
    {
        "access": "eyJ...",
        "refresh": "eyJ...",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "full_name": "Juan Pérez",
            "is_new_user": true
        }
    }
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Autenticación"],
        summary="Autenticación con Google OAuth2",
        description=(
            "Autentica al usuario usando un **token de identidad de Google OAuth2**. "
            "**No requiere autenticación previa.**\n\n"
            "Si el usuario no existe en el sistema, lo crea automáticamente usando "
            "el email y nombre de la cuenta de Google. "
            "El campo `is_new_user` en la respuesta indica si la cuenta fue creada en esta solicitud.\n\n"
            "Requiere que `GOOGLE_CLIENT_ID` esté configurado en el servidor."
        ),
        examples=[
            OpenApiExample(
                "Login con Google",
                value={"token": "google_id_token_here"},  # noqa
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Autenticación exitosa. Retorna access token, refresh token "
                "y datos del usuario (incluye is_new_user)."
            ),
            400: OpenApiResponse(description="Token no proporcionado o email no incluido en el token de Google."),
            401: OpenApiResponse(description="Token de Google inválido o expirado."),
            500: OpenApiResponse(description="Google OAuth no está configurado en el servidor o error interno."),
        },
    )
    def post(self, request):
        from django.conf import settings
        from google.auth.transport import requests
        from google.oauth2 import id_token

        token = request.data.get("token")

        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validar el token de Google
            CLIENT_ID = getattr(settings, "GOOGLE_CLIENT_ID", None)
            if not CLIENT_ID:
                logger.warning("GOOGLE_CLIENT_ID not configured")
                return Response(
                    {"error": "Google authentication not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

            email = id_info.get("email")
            full_name = id_info.get("name", "")

            if not email:
                return Response(
                    {"error": "Email not provided by Google"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Buscar o crear usuario
            try:
                user = User.objects.get(email=email)
                is_new_user = False
            except User.DoesNotExist:
                # Crear nuevo usuario
                user = User.objects.create_user(
                    email=email,
                    full_name=full_name,
                    password=None,  # No password for Google users
                    is_active=True,
                )
                is_new_user = True
                logger.info("New user created via Google OAuth: %s", email)

            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "is_new_user": is_new_user,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            logger.exception("Google token validation failed")
            return Response({"error": "Invalid Google token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.exception("Google auth error")
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CurrentUserView(APIView):
    """
    API endpoint para obtener información del usuario autenticado

    GET /api/me/

    Response (200 OK):
    {
        "id": 1,
        "email": "user@example.com",
        "full_name": "Juan Pérez",
        "role": "admin",
        "is_active": true
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Autenticación"],
        summary="Obtener usuario autenticado",
        description=(
            "Retorna los datos del usuario que está realizando la petición. **Requiere token JWT válido.**\n\n"
            "Útil para que el frontend cargue el perfil del usuario al iniciar sesión. "
            "Devuelve: `id`, `email`, `full_name`, `role`, `is_active` e `is_staff`."
        ),
        examples=[
            OpenApiExample(
                "Respuesta típica",
                value={
                    "id": 1,
                    "email": "admin@example.com",
                    "full_name": "Admin Sistema",
                    "role": "admin",
                    "is_active": True,
                    "is_staff": True,
                },
                response_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Datos del usuario autenticado actualmente."),
            401: OpenApiResponse(description="Token de acceso no proporcionado o inválido."),
        },
    )
    def get(self, request):
        user = request.user

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Certificados"],
        summary="Listar certificados",
        description=(
            "Retorna lista paginada de certificados. **El resultado varía según el rol:**\n"
            "- Administrador/coordinador: ve todos los certificados del sistema.\n"
            "- Participante: ve únicamente sus propios certificados.\n\n"
            "Cada item incluye datos del estudiante, evento, estado, código de verificación y URL del PDF."
        ),
        parameters=[
            OpenApiParameter(
                "page", OpenApiTypes.INT, description="Número de página (paginación de 20 items por defecto)."
            ),
        ],
        responses={200: CertificateListSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Certificados"],
        summary="Crear certificado manualmente",
        description=(
            "Crea un certificado asignando manualmente participante, evento y plantilla. "
            "Solo administradores y coordinadores pueden usar este endpoint. "
            "El certificado queda en estado `pending` hasta que se genere su PDF con el endpoint `/generate/`."
        ),
        request=CertificateCreateSerializer,
        responses={
            201: CertificateDetailSerializer,
            400: OpenApiResponse(description="Datos inválidos o relaciones no encontradas."),
            403: OpenApiResponse(description="Sin permisos para crear certificados."),
        },
    ),
    retrieve=extend_schema(
        tags=["Certificados"],
        summary="Detalle de certificado",
        description=(
            "Retorna todos los datos de un certificado específico incluyendo: "
            "datos del estudiante, evento, plantilla, estado actual, código de verificación, "
            "URL del PDF e historial completo de intentos de entrega."
        ),
        responses={
            200: CertificateDetailSerializer,
            404: OpenApiResponse(description="Certificado no encontrado."),
        },
    ),
    partial_update=extend_schema(
        tags=["Certificados"],
        summary="Actualizar certificado (parcial)",
        description=(
            "Actualiza uno o más campos de un certificado sin necesidad de enviar todos los datos. "
            "Solo administradores y coordinadores. Útil para corregir la plantilla o el estado manualmente."
        ),
        responses={
            200: CertificateDetailSerializer,
            400: OpenApiResponse(description="Datos inválidos."),
            403: OpenApiResponse(description="Sin permisos de modificación."),
        },
    ),
    destroy=extend_schema(
        tags=["Certificados"],
        summary="Eliminar certificado",
        description=(
            "Elimina permanentemente un certificado del sistema junto con sus registros de entrega asociados. "
            "**Acción irreversible.** Solo administradores."
        ),
        responses={
            204: OpenApiResponse(description="Certificado eliminado correctamente."),
            403: OpenApiResponse(description="Sin permisos para eliminar."),
            404: OpenApiResponse(description="Certificado no encontrado."),
        },
    ),
)
class CertificateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing certificates

    Endpoints:
    - GET /certificates/: List all certificates (paginated)
    - POST /certificates/: Create a certificate
    - GET /certificates/{id}/: Retrieve certificate details
    - PATCH /certificates/{id}/: Update certificate (admin only)
    - DELETE /certificates/{id}/: Delete certificate (admin only)

    Custom Actions:
    - POST /certificates/{id}/generate/: Generate certificate PDF
    - POST /certificates/{id}/deliver/: Deliver certificate via email/whatsapp/link
    - GET /certificates/{id}/history/: Get delivery history
    - GET /certificates/verify/{verification_code}/: Verify certificate by code (public)
    """

    queryset = Certificate.objects.all()

    def get_queryset(self):
        """
        Return queryset based on user and action
        Admin/coordinator sees all, Participante sees only THEIR certificates
        """
        if is_operational_user(self.request):
            return Certificate.objects.all().select_related("participant", "event", "template", "generated_by")

        # Participante: see only their own certificates
        if self.request.user and self.request.user.is_authenticated:
            user_email = self.request.user.email
            return Certificate.objects.filter(participant__email=user_email).select_related(
                "participant", "event", "template", "generated_by"
            )

        return Certificate.objects.none()

    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == "create":
            return CertificateCreateSerializer
        elif self.action == "generate":
            return CertificateGenerateSerializer
        elif self.action == "deliver":
            return CertificateDeliverSerializer
        elif self.action == "list":
            return CertificateListSerializer
        return CertificateDetailSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == "verify":
            self.permission_classes = [permissions.AllowAny]
        elif self.action == "export":
            self.permission_classes = [
                permissions.IsAuthenticated,
                permissions.IsAdminUser,
            ]
        elif self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
            "generate",
            "deliver",
            "retry",
        ]:
            if is_operational_user(self.request):
                self.permission_classes = [permissions.IsAuthenticated]
            else:
                self.permission_classes = [permissions.IsAdminUser]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @extend_schema(
        tags=["Certificados"],
        summary="Generar PDF del certificado",
        description=(
            "Genera el archivo PDF del certificado usando la plantilla asignada al evento. "
            "Si se envía `template_id` en el body, usa esa plantilla en lugar de la predeterminada.\n\n"
            "Al completarse, el estado del certificado cambia de `pending` a `generated` "
            "y la URL del PDF queda disponible en el campo `pdf_url`.\n\n"
            "**Requiere:** Administrador o coordinador."
        ),
        request=CertificateGenerateSerializer,
        responses={
            200: OpenApiResponse(
                description="PDF generado exitosamente. Retorna los datos actualizados del certificado."
            ),
            400: OpenApiResponse(description="Error al generar el PDF o plantilla especificada no encontrada."),
            403: OpenApiResponse(description="Sin permisos para generar certificados."),
            404: OpenApiResponse(description="Certificado no encontrado."),
        },
    )
    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        """
        Generate PDF for a certificate

        POST /certificates/{id}/generate/

        Optional body:
        {
            "template_id": "uuid" (optional, uses certificate's template by default)
        }
        """
        certificate = self.get_object()
        template_id = request.data.get("template_id")

        try:
            if template_id:
                from certificados.models import Template

                try:
                    template = Template.objects.get(id=template_id)
                    certificate.template = template
                except Template.DoesNotExist:
                    return Response(
                        {"status": "error", "message": "Plantilla no encontrada"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            certificate.generate(generated_by=request.user)
            log_action(
                "certificate_generated",
                user=request.user,
                certificate=certificate,
                ip_address=get_client_ip(request),
            )

            return Response(
                {
                    "status": "success",
                    "message": "Certificate generated successfully",
                    "certificate": CertificateDetailSerializer(certificate).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": f"Failed to generate certificate: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["Certificados"],
        summary="Entregar certificado al participante",
        description=(
            "Envía el certificado al participante usando el método de entrega especificado:\n"
            "- `email`: envía el PDF directamente al correo electrónico del participante.\n"
            "- `whatsapp`: envía un mensaje con el enlace al número de teléfono registrado.\n"
            "- `link`: genera una URL pública de descarga sin enviar notificación.\n\n"
            "Si se indica `recipient`, se usa ese email/teléfono en lugar del registrado. "
            "**El certificado debe haber sido generado previamente** (estado `generated`).\n\n"
            "Registra el intento en el historial de entregas (`DeliveryLog`)."
        ),
        request=CertificateDeliverSerializer,
        responses={
            200: OpenApiResponse(
                description="Certificado entregado exitosamente. Retorna datos del log "
                "de entrega y certificado actualizado."
            ),
            400: OpenApiResponse(description="Error al entregar, método inválido o certificado no generado."),
            403: OpenApiResponse(description="Sin permisos para entregar certificados."),
            404: OpenApiResponse(description="Certificado no encontrado."),
        },
    )
    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        """
        Deliver a certificate via email, whatsapp, or link

        POST /certificates/{id}/deliver/

        Required body:
        {
            "method": "email|whatsapp|link",
            "recipient": "optional custom recipient (email or phone)"
        }
        """
        certificate = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]
        recipient = serializer.validated_data.get("recipient")

        try:
            with transaction.atomic():
                certificate.deliver(method=method, recipient=recipient, sent_by=request.user)
                log_action(
                    "certificate_delivered",
                    user=request.user,
                    certificate=certificate,
                    ip_address=get_client_ip(request),
                    method=method,
                )

                return Response(
                    {
                        "status": "success",
                        "message": f"Certificate delivered via {method}",
                        "delivery_log": DeliveryLogSerializer(certificate.last_delivery_attempt).data,
                        "certificate": CertificateDetailSerializer(certificate).data,
                    },
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": f"Failed to deliver certificate: {str(e)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["Certificados"],
        summary="Historial de entregas del certificado",
        description=(
            "Retorna todos los intentos de entrega realizados para un certificado. "
            "Cada registro incluye: método usado (`email`/`whatsapp`/`link`), "
            "destinatario, estado del intento (`success`/`failed`/`pending`), "
            "fecha/hora y mensaje de error si falló.\n\n"
            "Útil para auditar qué pasó con cada certificado y cuántas veces se intentó enviar."
        ),
        responses={
            200: OpenApiResponse(
                description="Retorna total de intentos y lista de registros de entrega ordenados por fecha."
            ),
            404: OpenApiResponse(description="Certificado no encontrado."),
        },
    )
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """
        Get delivery history for a certificate

        GET /certificates/{id}/history/
        """
        certificate = self.get_object()
        delivery_logs = certificate.get_delivery_history()

        return Response(
            {
                "certificate_id": str(certificate.id),
                "total_attempts": delivery_logs.count(),
                "deliveries": DeliveryLogSerializer(delivery_logs, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Certificados"],
        summary="Reintentar entrega fallida",
        description=(
            "Reintenta la entrega de un certificado que falló previamente. "
            "**Solo aplica a certificados con estado `failed`.**\n\n"
            "Si se omite el campo `method` en el body, usa automáticamente el mismo método del último intento fallido. "
            "Si no hay intentos previos, el campo `method` es obligatorio.\n\n"
            "Registra el nuevo intento en el historial de entregas."
        ),
        request=CertificateRetrySerializer,
        examples=[
            OpenApiExample(
                "Reintentar con mismo método",
                value={},
                request_only=True,
            ),
            OpenApiExample(
                "Reintentar con método específico",
                value={"method": "whatsapp"},
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Reintento exitoso. Retorna el nuevo log de entrega y datos actualizados del certificado."
            ),
            400: OpenApiResponse(
                description="El certificado no está en estado failed, o no hay método "
                "disponible y no se proporcionó uno."
            ),
            404: OpenApiResponse(description="Certificado no encontrado."),
        },
    )
    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        """
        Retry delivery for a failed certificate.

        POST /certificates/{id}/retry/
        Body: {"method": "email|whatsapp|link"}  (optional — uses last failed method if omitted)
        """
        certificate = self.get_object()

        if certificate.status != "failed":
            return Response(
                {
                    "status": "error",
                    "message": "Only failed certificates can be retried",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        method = request.data.get("method")
        if not method:
            last = certificate.last_delivery_attempt
            if not last:
                return Response(
                    {
                        "status": "error",
                        "message": "No previous delivery found. Provide a method.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            method = last.delivery_method

        try:
            with transaction.atomic():
                certificate.deliver(method=method, sent_by=request.user)
                log_action(
                    "certificate_retried",
                    user=request.user,
                    certificate=certificate,
                    ip_address=get_client_ip(request),
                    method=method,
                )
                return Response(
                    {
                        "status": "success",
                        "message": f"Certificate retried via {method}",
                        "delivery_log": DeliveryLogSerializer(certificate.last_delivery_attempt).data,
                        "certificate": CertificateDetailSerializer(certificate).data,
                    },
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["Certificados"],
        summary="Exportar certificados (CSV o Excel)",
        description=(
            "Descarga todos los certificados en formato CSV o Excel para auditoría. "
            "**Solo administradores.**\n\n"
            "Columnas incluidas: id, nombre/email/documento del participante, nombre/fecha del evento, "
            "estado del certificado, código de verificación, URL del PDF, fecha de "
            "emisión y último estado de entrega.\n\n"
            "Soporta filtros opcionales por evento y estado."
        ),
        parameters=[
            OpenApiParameter(
                "file_format", OpenApiTypes.STR, description="Formato de exportación: `csv` (por defecto) o `excel`."
            ),
            OpenApiParameter("event_id", OpenApiTypes.INT, description="Filtrar certificados por ID de evento."),
            OpenApiParameter(
                "status", OpenApiTypes.STR, description="Filtrar por estado: `pending`, `generated`, `sent`, `failed`."
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Archivo descargable en el formato solicitado "
                "(Content-Type: text/csv o application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)."
            ),
            403: OpenApiResponse(description="Solo administradores pueden exportar certificados."),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="export",
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser],
    )
    def export(self, request):
        """
        Export certificates as CSV or Excel for administrator audit.

        GET /certificates/export/?file_format=csv&event_id=1&status=generated
        Query params:
          file_format — csv (default) | excel
          event_id    — filter by event
          status      — filter by certificate status
        """
        import csv
        import io

        from django.http import HttpResponse

        fmt = request.query_params.get("file_format", "csv").lower()
        event_id = request.query_params.get("event_id")
        cert_status = request.query_params.get("status")
        log_action(
            "export_requested",
            user=request.user,
            ip_address=get_client_ip(request),
            file_format=fmt,
            event_id=event_id,
            status_filter=cert_status,
        )

        qs = (
            Certificate.objects.select_related("participant", "event", "generated_by")
            .prefetch_related("deliveries")
            .order_by("-issued_at")
        )

        if event_id:
            qs = qs.filter(event_id=event_id)
        if cert_status:
            qs = qs.filter(status=cert_status)

        headers = [
            "id",
            "participant_name",
            "participant_email",
            "participant_document",
            "event_name",
            "event_date",
            "status",
            "verification_code",
            "pdf_url",
            "issued_at",
            "last_delivery_status",
        ]

        def row_for(cert):
            last = cert.deliveries.first()
            return [
                cert.id,
                f"{cert.participant.first_name} {cert.participant.last_name}",
                cert.participant.email,
                cert.participant.document_id,
                cert.event.name,
                cert.event.event_date.isoformat() if cert.event.event_date else "",
                cert.status,
                cert.verification_code,
                cert.pdf_url,
                cert.issued_at.isoformat(),
                last.status if last else "",
            ]

        if fmt == "excel":
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Certificados"
            ws.append(headers)
            for cert in qs:
                ws.append(row_for(cert))
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            response = HttpResponse(
                buf.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="certificados.xlsx"'
            return response

        # Default: CSV
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="certificados.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        for cert in qs:
            writer.writerow(row_for(cert))
        return response

    @extend_schema(
        tags=["Certificados"],
        summary="Verificar autenticidad de certificado (público)",
        description=(
            "Verifica si un certificado es auténtico usando su código de verificación único. "
            "**Endpoint público: no requiere autenticación.**\n\n"
            "Diseñado para que terceros (empleadores, instituciones) comprueben la validez de un certificado "
            "sin necesidad de ingresar al sistema. El código tiene formato `XXXX-XXXX-XXXX-XXXX`.\n\n"
            "Si el certificado está expirado, retorna `410 Gone` con los datos del certificado para referencia."
        ),
        parameters=[
            OpenApiParameter(
                "code",
                OpenApiTypes.STR,
                required=True,
                description="Código de verificación único del certificado (ej: `A1B2-C3D4-E5F6-G7H8`).",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Certificado válido y auténtico. Retorna datos completos del certificado."
            ),
            400: OpenApiResponse(description="Parámetro `code` no proporcionado."),
            404: OpenApiResponse(description="No existe ningún certificado con ese código de verificación."),
            410: OpenApiResponse(description="El certificado existe pero ha expirado."),
        },
    )
    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def verify(self, request):
        """
        Verify a certificate by verification code (public endpoint)

        GET /certificates/verify/?code=XXXX-XXXX-XXXX-XXXX
        """
        code = request.query_params.get("code")

        if not code:
            return Response(
                {
                    "status": "error",
                    "message": "Verification code is required (code query parameter)",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            certificate = Certificate.objects.get(verification_code=code)

            # Check if expired
            if certificate.is_expired():
                return Response(
                    {
                        "status": "error",
                        "message": "Certificate has expired",
                        "certificate": CertificateDetailSerializer(certificate).data,
                    },
                    status=status.HTTP_410_GONE,
                )

            return Response(
                {
                    "status": "success",
                    "message": "Certificate verified successfully",
                    "certificate": CertificateDetailSerializer(certificate).data,
                },
                status=status.HTTP_200_OK,
            )

        except Certificate.DoesNotExist:
            return Response(
                {"status": "error", "message": "Certificate not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def perform_destroy(self, instance):
        instance.delete(deleted_by=self.request.user)
        log_action(
            "certificate_deleted", user=self.request.user, certificate=instance, ip_address=get_client_ip(self.request)
        )

    @extend_schema(
        tags=["Certificados"],
        summary="Historial de cambios del certificado",
        description=(
            "Retorna el historial completo de cambios de datos del certificado: "
            "quién hizo cada cambio, cuándo (fecha y hora exacta con segundos) "
            "y qué campos cambiaron con sus valores anteriores y nuevos.\n\n"
            "Tipos de cambio: **Creado**, **Editado**, **Eliminado (baja lógica)**, **Restaurado**."
        ),
        responses={200: ChangelogSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="changelog")
    def changelog(self, request, pk=None):
        instance = self.get_object()
        return Response(ChangelogSerializer(instance.history.all().order_by("-history_date"), many=True).data)

    @extend_schema(
        tags=["Certificados"],
        summary="Restaurar certificado eliminado",
        description="Restaura un certificado eliminado con baja lógica. **Solo administradores.**",
        responses={
            200: OpenApiResponse(description="Certificado restaurado correctamente."),
            404: OpenApiResponse(description="No encontrado o no está eliminado."),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="restore",
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser],
    )
    def restore(self, request, pk=None):
        try:
            instance = Certificate.all_objects.get(pk=pk, is_deleted=True)
        except Certificate.DoesNotExist:
            return Response(
                {"error": "Certificado no encontrado o no está eliminado"}, status=status.HTTP_404_NOT_FOUND
            )
        instance.restore()
        log_action("certificate_restored", user=request.user, certificate=instance, ip_address=get_client_ip(request))
        return Response({"status": "success", "message": "Certificado restaurado correctamente"})


@extend_schema_view(
    list=extend_schema(
        tags=["Registros de Entrega"],
        summary="Listar registros de entrega",
        description=(
            "Retorna todos los registros de intentos de entrega, ordenados del más reciente al más antiguo. "
            "**Solo administradores.**\n\n"
            "Se puede filtrar por certificado usando el parámetro `certificate_id`. "
            "Cada registro incluye: certificado relacionado, método de entrega, destinatario, "
            "estado (`success`/`failed`/`pending`), fecha/hora y mensaje de error si aplica."
        ),
        parameters=[
            OpenApiParameter(
                "certificate_id",
                OpenApiTypes.STR,
                description="UUID del certificado para filtrar sus registros de entrega.",
            ),
        ],
        responses={200: DeliveryLogSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Registros de Entrega"],
        summary="Detalle de registro de entrega",
        description=(
            "Retorna todos los campos de un registro de entrega específico: "
            "método utilizado, destinatario, estado del intento, fecha/hora de envío, "
            "quién lo envió y mensaje de error si la entrega falló."
        ),
        responses={
            200: DeliveryLogSerializer,
            404: OpenApiResponse(description="Registro de entrega no encontrado."),
        },
    ),
)
class DeliveryLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing delivery logs (read-only)

    Endpoints:
    - GET /deliveries/: List all delivery logs (paginated)
    - GET /deliveries/{id}/: Retrieve a delivery log
    """

    queryset = DeliveryLog.objects.all().select_related("certificate", "sent_by").order_by("-sent_at")
    serializer_class = DeliveryLogSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        """Filter by certificate if cert_id query param provided"""
        queryset = super().get_queryset()

        cert_id = self.request.query_params.get("certificate_id")
        if cert_id:
            queryset = queryset.filter(certificate__id=cert_id)

        return queryset


@extend_schema_view(
    list=extend_schema(
        tags=["Eventos"],
        summary="Listar eventos",
        description=(
            "Retorna lista paginada de eventos académicos. **El resultado varía según el rol:**\n"
            "- Administrador/coordinador: ve todos los eventos del sistema.\n"
            "- Participante: ve solo los eventos en los que está inscrito.\n\n"
            "Soporta filtrado por `status` y `category`, búsqueda por nombre/descripción y ordenamiento. "
            "Cada evento incluye nombre del instructor y nombre de la plantilla asociada."
        ),
        parameters=[
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                description="Filtrar por estado: `draft`, `active`, `finished`, `cancelled`.",
            ),
            OpenApiParameter("category", OpenApiTypes.STR, description="Filtrar por categoría del evento."),
            OpenApiParameter(
                "search", OpenApiTypes.STR, description="Buscar texto en nombre y descripción del evento."
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description="Ordenar por: `event_date`, `created_at`, `name`. Prefijo `-` para descendente.",
            ),
        ],
        responses={200: EventSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Eventos"],
        summary="Crear evento",
        description=(
            "Crea un nuevo evento académico. El campo `created_by` se asigna automáticamente al usuario autenticado. "
            "Se puede asociar una plantilla de certificado (`template`) y un instructor "
            "(`instructor`) al crear el evento."
        ),
        request=EventSerializer,
        responses={
            201: EventSerializer,
            400: OpenApiResponse(description="Datos inválidos o relaciones no encontradas."),
        },
    ),
    retrieve=extend_schema(
        tags=["Eventos"],
        summary="Detalle de evento",
        description=(
            "Retorna todos los campos de un evento incluyendo: fechas, ubicación, estado, capacidad máxima, "
            "nombre legible del estado (`status_display`), nombre del instructor y nombre "
            "de la plantilla de certificados."
        ),
        responses={
            200: EventSerializer,
            404: OpenApiResponse(description="Evento no encontrado."),
        },
    ),
    update=extend_schema(
        tags=["Eventos"],
        summary="Actualizar evento completo",
        description="Actualiza todos los campos de un evento existente. Todos los campos son requeridos.",
        request=EventSerializer,
        responses={200: EventSerializer, 400: OpenApiResponse(description="Datos inválidos.")},
    ),
    partial_update=extend_schema(
        tags=["Eventos"],
        summary="Actualizar evento (parcial)",
        description="Actualiza uno o más campos de un evento sin necesidad de enviar "
        "todos los datos. Útil para cambiar solo el estado o la plantilla.",
        responses={200: EventSerializer, 400: OpenApiResponse(description="Datos inválidos.")},
    ),
    destroy=extend_schema(
        tags=["Eventos"],
        summary="Eliminar evento",
        description="Elimina permanentemente un evento y sus registros asociados. "
        "**Acción irreversible.** Solo administradores.",
        responses={
            204: OpenApiResponse(description="Evento eliminado correctamente."),
            404: OpenApiResponse(description="Evento no encontrado."),
        },
    ),
)
class EventsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events

    Endpoints:
    - GET /events/: List all events (paginated)
    - POST /events/: Create a new event
    - GET /events/{id}/: Retrieve event details
    - PUT /events/{id}/: Update an event
    - DELETE /events/{id}/: Delete an event

    Query Parameters:
    - status: Filter by event status (draft, active, finished, cancelled)
    - search: Search in name and description
    """

    queryset = Event.objects.select_related("category", "created_by", "instructor", "template").order_by("-event_date")
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "category", "is_deleted"]
    search_fields = ["name", "description"]
    ordering_fields = ["event_date", "created_at", "name"]
    ordering = ["-event_date"]

    def get_queryset(self):
        """Admin sees all (including deleted if show_deleted=true);
        coordinador sees all non-deleted; participante sees only enrolled."""
        from events.models import Enrollment

        if is_admin(self.request):
            if self.request.query_params.get("show_deleted") == "true":
                return Event.all_objects.select_related("category", "created_by", "instructor", "template").order_by(
                    "-event_date"
                )
            return super().get_queryset()

        queryset = super().get_queryset()

        if is_operational_user(self.request):
            return queryset

        if self.request.user and self.request.user.is_authenticated:
            enrolled_event_ids = Enrollment.objects.filter(participant__email=self.request.user.email).values_list(
                "event_id", flat=True
            )
            return queryset.filter(id__in=enrolled_event_ids)

        return queryset

    def get_permissions(self):
        """Events can be viewed by anyone authenticated; only admins can modify"""
        return [permissions.IsAuthenticated()]

    def _create_event_template(self, event, template_image, name_x, name_y, name_font_size, font_color):
        """Create or update a Template from event's template_image and settings"""
        from certificados.models import Template
        from django.core.files.storage import default_storage

        x_inch = name_x / 100 * 841.89 / 72 if name_x else 1.39
        y_inch = (1 - name_y / 100) * 595.28 / 72 if name_y else 2.08

        layout_config = {
            "participant_name": {
                "x": round(x_inch, 4),
                "y": round(y_inch, 4),
                "font_size": name_font_size or 24,
                "font_family": "Helvetica",
                "color": font_color or "#1e3a8a",
                "centered": True,
            }
        }

        if event.template:
            tpl = event.template
            if template_image:
                path = default_storage.save(f'events/templates/{template_image.name}', template_image)
                tpl.background_image = path
            tpl.layout_config = layout_config
            tpl.name = f"Evento: {event.name}"
            tpl.save()
            return tpl

        tpl = Template(
            name=f"Evento: {event.name}",
            background_image=template_image,
            layout_config=layout_config,
            x_coord=x_inch,
            y_coord=y_inch,
            font_size=name_font_size or 24,
            font_color=font_color or "#1e3a8a",
            is_active=False,
        )
        tpl.save()
        return tpl

    def perform_create(self, serializer):
        """Auto-assign created_by and create Template from template_image"""
        template_image = self.request.FILES.get('template_image')
        instance = serializer.save(created_by=self.request.user)
        if template_image:
            name_x = float(self.request.data.get('name_x', 50))
            name_y = float(self.request.data.get('name_y', 40))
            name_font_size = int(self.request.data.get('name_font_size', 24))
            font_color = self.request.data.get('font_color', '#1e3a8a')
            tpl = self._create_event_template(instance, template_image, name_x, name_y, name_font_size, font_color)
            instance.template = tpl
            instance.template_image = str(tpl.background_image)
            instance.save(update_fields=['template', 'template_image'])

    def perform_update(self, serializer):
        """Create/update Template from template_image and settings"""
        template_image = self.request.FILES.get('template_image')
        name_x = float(self.request.data.get('name_x', 50))
        name_y = float(self.request.data.get('name_y', 40))
        name_font_size = int(self.request.data.get('name_font_size', 24))
        font_color = self.request.data.get('font_color', '#1e3a8a')

        instance = serializer.save()
        if template_image or (instance.template and (name_x or name_y or name_font_size or font_color)):
            tpl = self._create_event_template(instance, template_image, name_x, name_y, name_font_size, font_color)
            instance.template = tpl
            if template_image:
                instance.template_image = str(tpl.background_image)
            instance.save(update_fields=['template', 'template_image'])

    @extend_schema(
        tags=["Eventos"],
        summary="Listar participantes del evento",
        description=(
            "Retorna todos los participantes inscritos en el evento con el estado de su certificado. "
            "Para cada participante incluye: datos de inscripción, asistencia marcada, "
            "id del certificado, estado del certificado y código de verificación si ya fue generado."
        ),
        responses={
            200: OpenApiResponse(
                description="Lista de objetos con: enrollment_id, participant_id, "
                "participant_name, participant_email, participant_phone, attendance, "
                "certificate_id, certificate_status, certificate_status_display, "
                "verification_code, has_certificate."
            ),
        },
        examples=[
            OpenApiExample(
                "Respuesta típica",
                value=[
                    {
                        "enrollment_id": 1,
                        "participant_id": 1,
                        "participant_id": 1,
                        "participant_name": "Juan Pérez",
                        "participant_email": "juan@example.com",
                        "participant_phone": "+123456789",
                        "attendance": True,
                        "certificate_id": "a1b2c3d4-...",
                        "certificate_status": "generated",
                        "certificate_status_display": "Generado",
                        "verification_code": "A1B2-C3D4-E5F6-G7H8",
                        "has_certificate": True,
                    }
                ],
                response_only=True,
            ),
        ],
    )
    @action(detail=True, methods=["get"], url_path="participants")
    def participants(self, request, pk=None):
        """
        Get all participants of an event with their certificate status
        GET /events/{id}/participants/
        Only the event creator can see participants
        """
        from events.models import Enrollment

        event = self.get_object()

        if event.created_by != request.user and not is_operational_user(request):
            return Response(
                {"detail": "No tienes permiso para ver los participantes de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        enrollments = Enrollment.objects.filter(event=event).select_related("participant")

        participants = []
        for enrollment in enrollments:
            certificate = Certificate.objects.filter(participant=enrollment.participant, event=event).first()

            participants.append(
                {
                    "enrollment_id": enrollment.id,
                    "participant_id": enrollment.participant.id,
                    "participant_name": enrollment.participant.full_name,
                    "participant_email": enrollment.participant.email,
                    "participant_phone": enrollment.participant.phone or "",
                    "attendance": enrollment.attendance,
                    "certificate_id": certificate.id if certificate else None,
                    "certificate_status": certificate.status if certificate else None,
                    "certificate_status_display": (certificate.get_status_display() if certificate else None),
                    "verification_code": (certificate.verification_code if certificate else None),
                    "has_certificate": certificate is not None,
                }
            )

        return Response(participants)

    @extend_schema(
        tags=["Eventos"],
        summary="Inscribir participante al evento",
        description=(
            "Inscribe un participante existente a este evento. **Solo administradores y coordinadores.**\n\n"
            "Se puede identificar al participante por `participant_id` o por `participant_email`. "
            "Si se usa email y el participante no existe, se crea uno nuevo automáticamente.\n\n"
            "Retorna error si el participante ya está inscrito en el evento."
        ),
        request=EventEnrollSerializer,
        examples=[
            OpenApiExample(
                "Inscribir por ID",
                value={"participant_id": 1},
                request_only=True,
            ),
            OpenApiExample(
                "Inscribir por email",
                value={"participant_email": "estudiante@example.com"},
                request_only=True,
            ),
        ],
        responses={
            201: EnrollmentSerializer,
            400: OpenApiResponse(description="Participante ya inscrito o falta participant_id / participant_email."),
            403: OpenApiResponse(description="Solo administradores o coordinadores pueden inscribir participantes."),
            404: OpenApiResponse(description="Participante no encontrado con el ID proporcionado."),
        },
    )
    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        """
        Enroll a participant to this event
        POST /events/{id}/enroll/
        Body: {"participant_id": 1} OR {"participant_email": "email@example.com"}
        Only the event creator can enroll participants
        """
        from events.models import Enrollment, Event
        from participants.models import Participant

        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({"error": "Evento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para inscribir participantes en este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        participant_id = request.data.get("participant_id")
        participant_email = request.data.get("participant_email")

        if participant_id:
            try:
                participant = Participant.objects.get(id=participant_id)
            except Participant.DoesNotExist:
                return Response(
                    {"error": "Participante no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif participant_email:
            import uuid

            doc_id = f"PART-{uuid.uuid4().hex[:8].upper()}"
            participant, created = Participant.objects.get_or_create(
                email=participant_email,
                defaults={
                    "document_id": doc_id,
                    "first_name": participant_email.split("@")[0],
                    "last_name": "",
                    "phone": "",
                    "is_active": True,
                },
            )
        else:
            return Response(
                {"error": "participant_id o participant_email es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment, created = Enrollment.objects.get_or_create(participant=participant, event=event)

        if not created:
            return Response(
                {"error": "El participante ya está inscrito"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Eventos"],
        summary="Generar certificados del evento",
        description=(
            "Genera certificados PDF para los participantes del evento que tienen "
            "asistencia marcada (`attendance=True`). "
            "**Solo administradores y coordinadores.**\n\n"
            "Si se envía `participant_ids` (lista de IDs), genera solo para esos participantes; "
            "de lo contrario genera para todos los que asistieron.\n\n"
            "Si el certificado ya existe y está en estado `pending`, lo genera. "
            "Si ya existe en otro estado, lo reporta en `already_exists` sin modificarlo.\n\n"
            "Retorna un resumen con conteo de creados, ya existentes y errores."
        ),
        request=EventGenerateCertificatesSerializer,
        examples=[
            OpenApiExample(
                "Generar para todos los asistentes",
                value={},
                request_only=True,
            ),
            OpenApiExample(
                "Generar para participantes específicos",
                value={"participant_ids": [1, 2, 3]},
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Resumen del proceso: event_id, event_name, "
                "total_enrollments, created, already_exists, errors y detalle de resultados."
            ),
            403: OpenApiResponse(description="Solo administradores o coordinadores pueden generar certificados."),
            404: OpenApiResponse(description="Evento no encontrado."),
        },
    )
    def _process_enrollment(self, enrollment, event, request):
        cert, created = Certificate.objects.get_or_create(
            participant=enrollment.participant,
            event=event,
            defaults={
                "status": "pending",
                "generated_by": request.user,
                "template": event.template,
            },
        )
        if created or cert.status == "pending":
            cert.generate(template=event.template, generated_by=request.user, skip_attendance_check=True)
            return {
                "type": "created",
                "participant_id": enrollment.participant.id,
                "participant_name": enrollment.participant.full_name,
                "certificate_id": cert.id,
                "status": cert.status,
            }
        return {
            "type": "already_exists",
            "participant_id": enrollment.participant.id,
            "participant_name": enrollment.participant.full_name,
            "certificate_id": cert.id,
            "status": cert.status,
        }

    @action(detail=True, methods=["post"], url_path="certificates/generate")
    def generate_certificates(self, request, pk=None):
        """
        Generate certificates for event participants (only those with attendance=True)
        POST /events/{id}/certificates/generate/
        Body: {"participant_ids": [1, 2, 3]} (optional, if empty generates for all with attendance)
        Only the event creator can generate certificates
        """

        from events.models import Enrollment, Event

        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({"error": "Evento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if event.created_by != request.user and not is_operational_user(request):
            return Response(
                {"error": "No tienes permiso para generar certificados de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )
        participant_ids = request.data.get("participant_ids", [])

        enrollments = Enrollment.objects.filter(event=event, attendance=True).select_related("participant")
        if participant_ids:
            enrollments = enrollments.filter(participant_id__in=participant_ids)

        results = {"created": [], "already_exists": [], "errors": []}

        for enrollment in enrollments:
            try:
                entry = self._process_enrollment(enrollment, event, request)
                results[entry.pop("type")].append(entry)
            except Exception as e:
                results["errors"].append(
                    {
                        "participant_id": enrollment.participant.id,
                        "participant_name": enrollment.participant.full_name,
                        "error": str(e),
                    }
                )

        return Response(
            {
                "event_id": event.id,
                "event_name": event.name,
                "total_enrollments": enrollments.count(),
                "created": len(results["created"]),
                "already_exists": len(results["already_exists"]),
                "errors": len(results["errors"]),
                "results": results,
            }
        )

    @extend_schema(
        tags=["Eventos"],
        summary="Enviar certificados del evento",
        description=(
            "Envía los certificados generados a los participantes del evento. "
            "**Solo administradores y coordinadores.**\n\n"
            "Parámetros del body:\n"
            "- `method`: método de entrega (`email`, `whatsapp` o `link`). Por defecto `email`.\n"
            "- `participant_ids`: lista de IDs para enviar solo a ciertos participantes (opcional).\n\n"
            "Si el certificado está en estado `pending`, lo genera primero y luego lo envía. "
            "Retorna un resumen con los enviados exitosamente y los que fallaron."
        ),
        request=EventSendCertificatesSerializer,
        examples=[
            OpenApiExample(
                "Enviar por email a todos",
                value={"method": "email"},
                request_only=True,
            ),
            OpenApiExample(
                "Enviar por WhatsApp a participantes específicos",
                value={"method": "whatsapp", "participant_ids": [1, 2, 3]},
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Resumen: event_id, event_name, method, total_sent, total_failed y detalle de resultados."
            ),
            403: OpenApiResponse(description="Solo administradores o coordinadores pueden enviar certificados."),
            404: OpenApiResponse(description="Evento no encontrado."),
        },
    )
    @action(detail=True, methods=["post"], url_path="certificates/send")
    def send_certificates(self, request, pk=None):
        """
        Send certificates to event participants
        POST /events/{id}/certificates/send/
        Body: {
            "method": "email|whatsapp|link",
            "participant_ids": [1, 2, 3] (optional, if empty sends to all with certificates)
        }
        Only the event creator can send certificates
        """

        from events.models import Event

        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({"error": "Evento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para enviar certificados de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )
        method = request.data.get("method", "email")
        participant_ids = request.data.get("participant_ids", [])

        certificates = Certificate.objects.filter(
            event=event, status__in=["generated", "sent", "pending"]
        ).select_related("participant")
        if participant_ids:
            certificates = certificates.filter(participant_id__in=participant_ids)

        results = {"sent": [], "failed": [], "created_and_sent": []}

        for cert in certificates:
            try:
                if cert.status == "pending":
                    cert.generate(generated_by=request.user)

                delivery_log = cert.deliver(method=method, sent_by=request.user)

                if delivery_log.status == "success":
                    results["sent"].append(
                        {
                            "certificate_id": cert.id,
                            "participant_name": cert.participant.full_name,
                            "recipient": cert.participant.email,
                        }
                    )
                else:
                    results["failed"].append(
                        {
                            "certificate_id": cert.id,
                            "participant_name": cert.participant.full_name,
                            "error": delivery_log.error_message or "Error al enviar",
                        }
                    )
            except Exception as e:
                results["failed"].append(
                    {
                        "certificate_id": cert.id,
                        "participant_name": cert.participant.full_name,
                        "error": str(e),
                    }
                )

        return Response(
            {
                "event_id": event.id,
                "event_name": event.name,
                "method": method,
                "total_sent": len(results["sent"]),
                "total_failed": len(results["failed"]),
                "results": results,
            }
        )

    @extend_schema(
        tags=["Eventos"],
        summary="Registros de entrega del evento",
        description=(
            "Retorna todos los registros de entrega de los certificados de este evento, "
            "ordenados del más reciente al más antiguo. "
            "Permite ver en un solo lugar el estado de todas las entregas realizadas para el evento."
        ),
        responses={200: DeliveryLogSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="deliveries")
    def event_deliveries(self, request, pk=None):
        """
        Get all delivery logs for an event's certificates
        GET /events/{id}/deliveries/
        Only the event creator can see deliveries
        """
        event = self.get_object()

        if event.created_by != request.user:
            return Response(
                {"detail": "No tienes permiso para ver las entregas de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        certificates = Certificate.objects.filter(event=event)

        deliveries = (
            DeliveryLog.objects.filter(certificate__in=certificates)
            .select_related("certificate", "sent_by")
            .order_by("-sent_at")
        )

        serializer = DeliveryLogSerializer(deliveries, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Eventos"],
        summary="Estadísticas del evento",
        description=(
            "Retorna un resumen estadístico completo del evento:\n"
            "- `total_enrollments`: total de participantes inscritos.\n"
            "- `attendees`: participantes con asistencia marcada.\n"
            "- `absent`: participantes que no asistieron.\n"
            "- `total_certificates`: total de certificados creados.\n"
            "- `generated_certificates`: certificados con PDF generado.\n"
            "- `sent_certificates`: certificados entregados exitosamente.\n"
            "- `pending_certificates`: certificados pendientes de generación.\n"
            "- `failed_certificates`: certificados con entrega fallida."
        ),
        responses={200: OpenApiResponse(description="Objeto con las métricas estadísticas del evento.")},
    )
    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        """
        Get event statistics
        GET /events/{id}/stats/
        """
        from events.models import Enrollment

        event = self.get_object()
        enrollments = Enrollment.objects.filter(event=event)
        certificates = Certificate.objects.filter(event=event)

        attendees = enrollments.filter(attendance=True).count()
        total_enrollments = enrollments.count()
        total_certificates = certificates.count()
        generated_certificates = certificates.filter(status="generated").count()
        sent_certificates = certificates.filter(status="sent").count()
        pending_certificates = certificates.filter(status="pending").count()
        failed_certificates = certificates.filter(status="failed").count()

        return Response(
            {
                "event_id": event.id,
                "event_name": event.name,
                "total_enrollments": total_enrollments,
                "attendees": attendees,
                "absent": total_enrollments - attendees,
                "total_certificates": total_certificates,
                "generated_certificates": generated_certificates,
                "sent_certificates": sent_certificates,
                "pending_certificates": pending_certificates,
                "failed_certificates": failed_certificates,
            }
        )

    @extend_schema(
        tags=["Eventos"],
        summary="Listar invitaciones del evento",
        description=(
            "Retorna todas las invitaciones enviadas para este evento. "
            "Cada invitación incluye: email del invitado, token único, estado "
            "(`pending`/`sent`/`accepted`/`rejected`/`expired`), fechas de envío y respuesta, "
            "y datos del participante si ya está registrado."
        ),
        responses={200: EventInvitationSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="invitations")
    def invitations(self, request, pk=None):
        """
        Get all invitations for an event
        GET /events/{id}/invitations/
        Only the event creator can see invitations
        """
        from events.models import EventInvitation

        event = self.get_object()

        if event.created_by != request.user:
            return Response(
                {"detail": "No tienes permiso para ver las invitaciones de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        invitations = EventInvitation.objects.filter(event=event).select_related("participant")

        serializer = EventInvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    @staticmethod
    def _parse_emails_from_file(file):
        """Extract emails from an uploaded CSV or Excel file. Returns (emails, error_msg)."""
        import pandas as pd

        try:
            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
            email_col = next((col for col in df.columns if "email" in col.lower()), None)
            if not email_col:
                return [], "No se encontró columna de email en el archivo"
            return df[email_col].dropna().tolist(), None
        except Exception as e:
            return [], f"Error leyendo archivo: {str(e)}"

    @staticmethod
    def _parse_emails_from_json(emails_json):
        """Extract emails from a JSON value. Returns list (empty on error)."""
        try:
            if isinstance(emails_json, str):
                emails_json = json.loads(emails_json)
            return list(emails_json) if isinstance(emails_json, list) else []
        except ValueError:
            logger.warning("Invalid JSON format in emails field")
            return []

    @staticmethod
    def _send_invitation_email(invitation, event, frontend_url, expires_days, settings):
        """Send an invitation email. Returns error string, or None on success."""
        from services.email_service import EmailService

        try:
            invitation_link = f"{frontend_url}/invitation/{invitation.token}"
            subject = f"Invitación al evento: {event.name}"
            message = f"""
Hola,

Has sido invitado al evento "{event.name}".

Fecha: {event.event_date}
Ubicación: {event.location or 'Por definir'}

Para aceptar esta invitación, haz clic en el siguiente enlace:
{invitation_link}

Esta invitación expira en {expires_days} días.

Saludos,
Equipo CertyPro
"""
            result = EmailService.send_email(subject, message, invitation.email)
            if result["success"]:
                return None
            return f"Error enviando a {invitation.email}: {result['message']}"
        except Exception as e:
            return f"Error enviando a {invitation.email}: {str(e)}"

    @extend_schema(
        tags=["Eventos"],
        summary="Enviar invitaciones al evento",
        description=(
            "Envía invitaciones por email a una lista de destinatarios. Los emails pueden venir de:\n"
            "- **Archivo** (`file`): CSV o Excel con una columna de email.\n"
            "- **Lista JSON** (`emails`): array de strings con emails directamente en el body.\n"
            "Ambas fuentes se pueden combinar en una sola petición (multipart/form-data).\n\n"
            "Por cada email válido crea una invitación con token único y la envía. "
            "La invitación expira en **7 días**. Si ya existe una invitación para ese "
            "email en el evento, la omite y lo reporta en `errors`."
        ),
        request=EventSendInvitationsSerializer,
        examples=[
            OpenApiExample(
                "Enviar desde lista JSON",
                value={"emails": ["invitado1@example.com", "invitado2@example.com"]},
                request_only=True,
            ),
            OpenApiExample(
                "Enviar desde archivo + lista combinados",
                value={"file": "(archivo .xlsx)", "emails": ["extra@example.com"]},
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Resumen: total de emails procesados, creados exitosamente y lista de errores."
            ),
            400: OpenApiResponse(description="No se encontraron emails válidos o error al leer el archivo."),
        },
    )
    @action(detail=True, methods=["post"], url_path="invitations/send")
    def send_invitations(self, request, pk=None):
        """
        Send invitations from Excel/CSV file or email list
        POST /events/{id}/invitations/send/
        Body (form-data):
        - file: Excel/CSV file (optional)
        - emails: JSON array of emails (optional, e.g., ["email1@test.com", "email2@test.com"])
        Only the event creator can send invitations
        """
        import uuid
        from datetime import timedelta

        from django.conf import settings
        from django.utils import timezone

        from events.models import EventInvitation

        event = self.get_object()

        if event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para enviar invitaciones de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )
        emails = []

        if "file" in request.FILES:
            file_emails, file_error = self._parse_emails_from_file(request.FILES["file"])
            if file_error:
                return Response({"error": file_error}, status=status.HTTP_400_BAD_REQUEST)
            emails = file_emails

        if "emails" in request.data:
            emails.extend(self._parse_emails_from_json(request.data.get("emails")))

        if not emails:
            return Response(
                {"error": "No se encontraron emails para enviar invitaciones"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_days = 7
        expires_at = timezone.now() + timedelta(days=expires_days)
        created = 0
        errors = []
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")

        for email in emails:
            email = str(email).strip().lower()
            if not email or "@" not in email:
                errors.append(f"Email inválido: {email}")
                continue

            if EventInvitation.objects.filter(event=event, email=email).exists():
                errors.append(f"Ya existe invitación para: {email}")
                continue

            participant = Participant.objects.filter(email__iexact=email).first()
            invitation = EventInvitation.objects.create(
                event=event,
                participant=participant,
                email=email,
                token=uuid.uuid4(),
                status="pending",
                expires_at=expires_at,
                created_by=request.user,
            )

            send_error = self._send_invitation_email(invitation, event, frontend_url, expires_days, settings)
            if send_error:
                errors.append(send_error)
            else:
                invitation.status = "sent"
                invitation.sent_at = timezone.now()
                invitation.save()

            created += 1

        return Response({"total": len(emails), "created": created, "errors": errors})

    @extend_schema(
        tags=["Eventos"],
        summary="Enviar todas las invitaciones pendientes",
        description=(
            "Envía por email todas las invitaciones del evento que están en estado `pending`. "
            "Útil para reenviar invitaciones que no fueron enviadas en el momento de crearlas. "
            "Actualiza la fecha de expiración a 7 días desde ahora antes de enviar. "
            "Retorna el conteo de enviadas exitosamente y la lista de errores."
        ),
        responses={
            200: OpenApiResponse(description="Resumen: sent (enviadas) y errors (lista de errores por email)."),
            400: OpenApiResponse(description="No hay invitaciones pendientes para este evento."),
        },
    )
    @action(detail=True, methods=["post"], url_path="invitations/send-all")
    def send_all_invitations(self, request, pk=None):
        """
        Send pending invitations for an event
        POST /events/{id}/invitations/send-all/
        Only the event creator can send invitations
        """
        import uuid
        from datetime import timedelta

        from django.conf import settings
        from django.utils import timezone

        from events.models import EventInvitation

        event = self.get_object()

        if event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para enviar invitaciones de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )
        pending = EventInvitation.objects.filter(event=event, status="pending")

        if not pending.exists():
            return Response(
                {"message": "No hay invitaciones pendientes"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        expires_at = timezone.now() + timedelta(days=7)
        sent = 0
        errors = []

        for invitation in pending:
            invitation.expires_at = expires_at
            if not invitation.participant:
                invitation.participant = Participant.objects.filter(email__iexact=invitation.email).first()
            if not invitation.token:
                invitation.token = uuid.uuid4()

            send_error = self._send_invitation_email(invitation, event, frontend_url, 7, settings)
            if send_error:
                errors.append(send_error)
            else:
                invitation.status = "sent"
                invitation.sent_at = timezone.now()
                invitation.save()
                sent += 1

        return Response({"sent": sent, "errors": errors})

    @extend_schema(
        tags=["Eventos"],
        summary="Finalizar evento",
        description=(
            "Marca el evento como finalizado (`status = finished`). "
            "Si `send_certificates` es `true` en el body, genera y envía automáticamente por email "
            "los certificados de todos los participantes con asistencia marcada.\n\n"
            "Retorna error si el evento ya está en estado `finished`."
        ),
        request=EventFinalizeSerializer,
        examples=[
            OpenApiExample(
                "Finalizar sin enviar certificados",
                value={"send_certificates": False},
                request_only=True,
            ),
            OpenApiExample(
                "Finalizar y enviar certificados automáticamente",
                value={"send_certificates": True},
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Evento finalizado. Retorna event_id, status y "
                "certificates_sent (cantidad de certificados enviados)."
            ),
            400: OpenApiResponse(description="El evento ya está finalizado."),
            404: OpenApiResponse(description="Evento no encontrado."),
        },
    )
    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize_event(self, request, pk=None):
        """
        Finalize event and optionally send certificates
        POST /events/{id}/finalize/
        Body: {"send_certificates": true/false}
        Only the event creator can finalize an event
        """
        from django.utils import timezone

        from events.models import Enrollment

        event = self.get_object()

        if event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para finalizar este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if event.status == "finished":
            return Response(
                {"error": "El evento ya está finalizado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_certificates = request.data.get("send_certificates", False)

        # Update event status
        event.status = "finished"
        event.save()

        result = {"event_id": event.id, "status": "finished", "certificates_sent": 0}

        # Send certificates if requested
        if send_certificates:
            enrollments = Enrollment.objects.filter(event=event, attendance=True)

            for enrollment in enrollments:
                # Get or create certificate for this student
                certificate, _ = Certificate.objects.get_or_create(
                    participant=enrollment.participant,
                    event=event,
                    defaults={
                        "template": event.template,
                        "status": "pending",
                    },
                )

                try:
                    # Generate if not already generated
                    if certificate.status == "pending":
                        certificate.generate(generated_by=request.user)

                    # Send
                    delivery_log = certificate.deliver(method="email", sent_by=request.user)

                    if delivery_log.status == "success":
                        enrollment.certificate_sent = True
                        enrollment.certificate_sent_at = timezone.now()
                        enrollment.certificate_sent_method = "email"
                        enrollment.save()
                        result["certificates_sent"] += 1
                    else:
                        logger.error(
                            "Failed to send certificate %s: %s",
                            certificate.id,
                            delivery_log.error_message,
                        )
                except Exception as e:
                    logger.exception("Error processing certificate %s", certificate.id)

        return Response(result)

    def perform_destroy(self, instance):
        instance.delete(deleted_by=self.request.user)
        log_action("event_deleted", user=self.request.user, ip_address=get_client_ip(self.request))

    @extend_schema(
        tags=["Eventos"],
        summary="Historial de cambios del evento",
        description=(
            "Retorna el historial completo de cambios del evento: nombre, fechas, estado, instructor, plantilla, etc. "
            "Muestra quién hizo cada cambio, cuándo (fecha y hora exacta con segundos) "
            "y los valores anteriores y nuevos de cada campo modificado.\n\n"
            "Tipos de cambio: **Creado**, **Editado**, **Eliminado (baja lógica)**, **Restaurado**."
        ),
        responses={200: ChangelogSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="changelog")
    def changelog(self, request, pk=None):
        instance = self.get_object()
        return Response(ChangelogSerializer(instance.history.all().order_by("-history_date"), many=True).data)

    @extend_schema(
        tags=["Eventos"],
        summary="Restaurar evento eliminado",
        description="Restaura un evento eliminado con baja lógica. **Solo administradores.**",
        responses={
            200: OpenApiResponse(description="Evento restaurado correctamente."),
            404: OpenApiResponse(description="No encontrado o no está eliminado."),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="restore",
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser],
    )
    def restore(self, request, pk=None):
        try:
            instance = Event.all_objects.get(pk=pk, is_deleted=True)
        except Event.DoesNotExist:
            return Response({"error": "Evento no encontrado o no está eliminado"}, status=status.HTTP_404_NOT_FOUND)
        instance.restore()
        log_action("event_restored", user=request.user, ip_address=get_client_ip(request))
        return Response({"status": "success", "message": "Evento restaurado correctamente"})


@extend_schema_view(
    list=extend_schema(
        tags=["Participantes"],
        summary="Listar participantes",
        description=(
            "Retorna lista paginada de participantes/estudiantes registrados. **El resultado varía según el rol:**\n"
            "- Administrador/coordinador: ve todos los participantes del sistema.\n"
            "- Otros usuarios: ven solo los participantes de sus propios eventos.\n\n"
            "Soporta búsqueda por nombre, email o documento de identidad, y filtrado por estado activo."
        ),
        parameters=[
            OpenApiParameter(
                "is_active", OpenApiTypes.BOOL, description="Filtrar por estado activo: `true` o `false`."
            ),
            OpenApiParameter(
                "search", OpenApiTypes.STR, description="Buscar en nombre, apellido, email o documento de identidad."
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description="Ordenar por: `first_name`, `last_name`, `created_at`. Prefijo `-` para descendente.",
            ),
        ],
        responses={200: ParticipantSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Participantes"],
        summary="Crear participante",
        description=(
            "Registra un nuevo participante/estudiante en el sistema. "
            "El campo `created_by` se asigna automáticamente al usuario autenticado. "
            "El `document_id` y el `email` deben ser únicos en el sistema."
        ),
        request=ParticipantSerializer,
        responses={
            201: ParticipantSerializer,
            400: OpenApiResponse(description="Datos inválidos, email o documento de identidad ya registrado."),
        },
    ),
    retrieve=extend_schema(
        tags=["Participantes"],
        summary="Detalle de participante",
        description="Retorna todos los datos de un participante: documento de identidad, "
        "nombre completo, email, teléfono, estado activo y fechas de creación.",
        responses={
            200: ParticipantSerializer,
            404: OpenApiResponse(description="Participante no encontrado."),
        },
    ),
    update=extend_schema(
        tags=["Participantes"],
        summary="Actualizar participante completo",
        description="Actualiza todos los campos de un participante existente. Todos los campos son requeridos.",
        request=ParticipantSerializer,
        responses={200: ParticipantSerializer, 400: OpenApiResponse(description="Datos inválidos.")},
    ),
    partial_update=extend_schema(
        tags=["Participantes"],
        summary="Actualizar participante (parcial)",
        description="Actualiza uno o más campos de un participante sin enviar todos los datos.",
        responses={200: ParticipantSerializer},
    ),
    destroy=extend_schema(
        tags=["Participantes"],
        summary="Eliminar participante",
        description="Elimina permanentemente un participante del sistema. "
        "**Acción irreversible.** Solo administradores.",
        responses={
            204: OpenApiResponse(description="Participante eliminado correctamente."),
            404: OpenApiResponse(description="Participante no encontrado."),
        },
    ),
)
class ParticipantsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students

    Endpoints:
    - GET /students/: List all students (paginated)
    - POST /students/: Create a new student
    - GET /students/{id}/: Retrieve student details
    - PUT /students/{id}/: Update a student
    - DELETE /students/{id}/: Delete a student
    - POST /students/import/: Bulk import students from Excel

    Query Parameters:
    - search: Search by name, email, or document_id
    - is_active: Filter by active status (true/false)
    """

    queryset = Participant.objects.all().order_by("first_name", "last_name")
    serializer_class = ParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["is_active", "is_deleted"]
    search_fields = ["first_name", "last_name", "email", "document_id"]
    ordering_fields = ["first_name", "last_name", "created_at"]
    ordering = ["first_name", "last_name"]

    def get_queryset(self):
        """Admin sees all (including deleted if show_deleted=true); coordinator sees only their own."""
        if is_admin(self.request):
            if self.request.query_params.get("show_deleted") == "true":
                return Participant.all_objects.all().order_by("first_name", "last_name")
            return super().get_queryset()

        user_events = Event.objects.filter(created_by=self.request.user).values_list("id", flat=True)
        return (
            super()
            .get_queryset()
            .filter(models.Q(created_by=self.request.user) | models.Q(enrollments__event_id__in=user_events))
            .distinct()
        )

    def get_permissions(self):
        """Only admins can modify"""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            if is_operational_user(self.request):
                permission_classes = [permissions.IsAuthenticated]
            else:
                permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Auto-assign created_by to current user"""
        serializer.save(created_by=self.request.user)

    def _parse_import_file(self, file):
        import pandas as pd

        if file.name.endswith((".xlsx", ".xls")):
            return pd.read_excel(file)
        return pd.read_csv(file)

    def _normalize_import_row(self, row):
        doc_id = str(row.get("document_id", row.get("documento", ""))).strip()
        email = str(row.get("email", "")).strip()
        first_name = str(row.get("first_name", row.get("nombre", ""))).strip()
        last_name = str(row.get("last_name", row.get("apellido", ""))).strip()

        if not first_name and not last_name:
            full = str(row.get("full_name", row.get("nombre_completo", ""))).strip()
            if full:
                parts = full.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

        phone = str(row.get("phone", row.get("telefono", ""))).strip()
        if phone.lower() in ("nan", "none", ""):
            phone = ""

        return doc_id, email, first_name, last_name, phone

    @extend_schema(
        tags=["Participantes"],
        summary="Importar participantes desde Excel/CSV",
        description=(
            "Importa masivamente participantes desde un archivo Excel (`.xlsx`/`.xls`) o CSV. "
            "**Solo administradores.**\n\n"
            "**Columnas requeridas en el archivo:**\n"
            "- `document_id` o `documento`: documento de identidad único.\n"
            "- `email`: correo electrónico.\n"
            "- `first_name`/`last_name` o `nombre`/`apellido` o `full_name`/`nombre_completo`.\n\n"
            "**Columnas opcionales:** `phone` o `telefono`.\n\n"
            "Los nombres de columna son insensibles a mayúsculas y espacios. "
            "Si un `document_id` ya existe, se omite esa fila (no duplica). "
            "Los errores por fila no detienen el procesamiento de las demás filas.\n\n"
            "Retorna el total de filas procesadas, cuántas se importaron y los errores detallados por fila."
        ),
        responses={
            200: OpenApiResponse(
                description="Resultado: total_rows, imported (creados), errors (lista de {row, error})."
            ),
            400: OpenApiResponse(description="No se proporcionó archivo o error al leer el formato."),
            403: OpenApiResponse(description="Solo administradores pueden importar participantes."),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="import_students",
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser],
    )
    def import_students(self, request):
        from django.db import IntegrityError

        if "file" not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["file"]
        imported = 0
        errors = []

        try:
            df = self._parse_import_file(file)
            df.columns = [str(c).strip().lower() for c in df.columns]

            for idx, row in df.iterrows():
                try:
                    doc_id, email, first_name, last_name, phone = self._normalize_import_row(row)

                    if not doc_id or not email:
                        errors.append({"row": idx + 2, "error": "Faltan document_id o email"})
                        continue

                    _, created = Participant.objects.get_or_create(
                        document_id=doc_id,
                        defaults={
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": email,
                            "phone": phone,
                            "created_by": request.user,
                        },
                    )
                    if created:
                        imported += 1
                except IntegrityError:
                    errors.append(
                        {
                            "row": idx + 2,
                            "error": f"Email o documento duplicado: {email}",
                        }
                    )
                except Exception as e:
                    errors.append({"row": idx + 2, "error": str(e)})

            return Response(
                {"total_rows": len(df), "imported": imported, "errors": errors},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to process file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_destroy(self, instance):
        instance.delete(deleted_by=self.request.user)
        log_action("participant_deleted", user=self.request.user, ip_address=get_client_ip(self.request))

    @extend_schema(
        tags=["Participantes"],
        summary="Historial de cambios del participante",
        description=(
            "Retorna el historial completo de cambios de datos del participante: nombre, email, documento, etc. "
            "Incluye quién hizo cada cambio y cuándo (fecha y hora exacta con segundos)."
        ),
        responses={200: ChangelogSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="changelog")
    def changelog(self, request, pk=None):
        instance = self.get_object()
        return Response(ChangelogSerializer(instance.history.all().order_by("-history_date"), many=True).data)

    @extend_schema(
        tags=["Participantes"],
        summary="Restaurar participante eliminado",
        description="Restaura un participante eliminado con baja lógica. **Solo administradores.**",
        responses={
            200: OpenApiResponse(description="Participante restaurado correctamente."),
            404: OpenApiResponse(description="No encontrado o no está eliminado."),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="restore",
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser],
    )
    def restore(self, request, pk=None):
        try:
            instance = Participant.all_objects.get(pk=pk, is_deleted=True)
        except Participant.DoesNotExist:
            return Response(
                {"error": "Participante no encontrado o no está eliminado"}, status=status.HTTP_404_NOT_FOUND
            )
        instance.restore()
        log_action("participant_restored", user=request.user, ip_address=get_client_ip(request))
        return Response({"status": "success", "message": "Participante restaurado correctamente"})


@extend_schema_view(
    list=extend_schema(
        tags=["Instructores"],
        summary="Listar instructores",
        description=(
            "Retorna la lista de instructores registrados. "
            "Administradores/coordinadores ven todos; otros usuarios solo ven los que ellos crearon. "
            "Soporta búsqueda por nombre completo, email y especialidad."
        ),
        parameters=[
            OpenApiParameter(
                "search", OpenApiTypes.STR, description="Buscar por nombre completo, email o especialidad."
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description="Ordenar por: `full_name`, `created_at`. Prefijo `-` para descendente.",
            ),
        ],
        responses={200: InstructorSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Instructores"],
        summary="Crear instructor",
        description=(
            "Registra un nuevo instructor en el sistema. "
            "El campo `created_by` se asigna automáticamente. "
            "Los instructores pueden ser asociados a eventos para aparecer en la firma de los certificados."
        ),
        request=InstructorSerializer,
        responses={201: InstructorSerializer, 400: OpenApiResponse(description="Datos inválidos.")},
    ),
    retrieve=extend_schema(
        tags=["Instructores"],
        summary="Detalle de instructor",
        description="Retorna todos los campos de un instructor: nombre completo, email, "
        "especialidad y datos de auditoría.",
        responses={200: InstructorSerializer, 404: OpenApiResponse(description="Instructor no encontrado.")},
    ),
    update=extend_schema(
        tags=["Instructores"],
        summary="Actualizar instructor completo",
        description="Actualiza todos los campos de un instructor. Todos los campos son requeridos.",
        request=InstructorSerializer,
        responses={200: InstructorSerializer},
    ),
    partial_update=extend_schema(
        tags=["Instructores"],
        summary="Actualizar instructor (parcial)",
        description="Actualiza uno o más campos de un instructor sin necesidad de enviar todos los datos.",
        responses={200: InstructorSerializer},
    ),
    destroy=extend_schema(
        tags=["Instructores"],
        summary="Eliminar instructor",
        description="Elimina permanentemente un instructor del sistema. Solo administradores.",
        responses={
            204: OpenApiResponse(description="Instructor eliminado correctamente."),
            404: OpenApiResponse(description="Instructor no encontrado."),
        },
    ),
)
class InstructorsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing instructors

    Endpoints:
    - GET /instructors/: List all instructors
    - POST /instructors/: Create a new instructor
    - GET /instructors/{id}/: Retrieve instructor details
    - PUT /instructors/{id}/: Update an instructor
    - DELETE /instructors/{id}/: Delete an instructor

    Query Parameters:
    - search: Search by name, email, or specialty
    """

    queryset = Instructor.objects.all().order_by("full_name")
    serializer_class = InstructorSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["full_name", "email", "specialty"]
    ordering_fields = ["full_name", "created_at"]
    ordering = ["full_name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not is_operational_user(self.request):
            queryset = queryset.filter(created_by=self.request.user)
        return queryset

    def get_permissions(self):
        """Only admins can modify"""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            if is_operational_user(self.request):
                permission_classes = [permissions.IsAuthenticated]
            else:
                permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Auto-assign created_by to current user"""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.delete(deleted_by=self.request.user)
        log_action("instructor_deleted", user=self.request.user, ip_address=get_client_ip(self.request))

    @extend_schema(
        tags=["Instructores"],
        summary="Historial de cambios del instructor",
        description=(
            "Retorna el historial completo de cambios de datos del instructor: nombre, email, especialidad, etc. "
            "Incluye quién hizo cada cambio y cuándo (fecha y hora exacta con segundos)."
        ),
        responses={200: ChangelogSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="changelog")
    def changelog(self, request, pk=None):
        instance = self.get_object()
        return Response(ChangelogSerializer(instance.history.all().order_by("-history_date"), many=True).data)

    @extend_schema(
        tags=["Instructores"],
        summary="Restaurar instructor eliminado",
        description="Restaura un instructor eliminado con baja lógica. **Solo administradores.**",
        responses={
            200: OpenApiResponse(description="Instructor restaurado correctamente."),
            404: OpenApiResponse(description="No encontrado o no está eliminado."),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="restore",
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser],
    )
    def restore(self, request, pk=None):
        try:
            from instructors.models import Instructor

            instance = Instructor.all_objects.get(pk=pk, is_deleted=True)
        except Instructor.DoesNotExist:
            return Response({"error": "Instructor no encontrado o no está eliminado"}, status=status.HTTP_404_NOT_FOUND)
        instance.restore()
        log_action("instructor_restored", user=request.user, ip_address=get_client_ip(request))
        return Response({"status": "success", "message": "Instructor restaurado correctamente"})


@extend_schema_view(
    list=extend_schema(
        tags=["Plantillas"],
        summary="Listar plantillas de certificado",
        description=(
            "Retorna las plantillas de certificados disponibles. "
            "Administradores ven todas; otros usuarios solo las que ellos crearon. "
            "Soporta filtrado por estado activo y categoría, y búsqueda por nombre."
        ),
        parameters=[
            OpenApiParameter(
                "is_active", OpenApiTypes.BOOL, description="Filtrar plantillas activas (`true`) o inactivas (`false`)."
            ),
            OpenApiParameter("category", OpenApiTypes.STR, description="Filtrar por categoría de la plantilla."),
            OpenApiParameter("search", OpenApiTypes.STR, description="Buscar por nombre o categoría."),
        ],
        responses={200: TemplateSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Plantillas"],
        summary="Crear plantilla de certificado",
        description=(
            "Crea una nueva plantilla con la configuración de texto para el nombre del participante: "
            "coordenadas `x_coord`/`y_coord` (en pulgadas sobre el PDF), tamaño de fuente, "
            "familia tipográfica y color. Luego se sube la imagen de fondo con `/upload-image/`."
        ),
        request=TemplateCreateSerializer,
        responses={201: TemplateSerializer, 400: OpenApiResponse(description="Datos inválidos.")},
    ),
    retrieve=extend_schema(
        tags=["Plantillas"],
        summary="Detalle de plantilla",
        description=(
            "Retorna todos los campos de una plantilla: nombre, categoría, estado activo, "
            "configuración de fuente y coordenadas, `layout_config` completo (JSON), "
            "y URL de la imagen de fondo (`background_image_url`)."
        ),
        responses={200: TemplateSerializer, 404: OpenApiResponse(description="Plantilla no encontrada.")},
    ),
    update=extend_schema(
        tags=["Plantillas"],
        summary="Actualizar plantilla completa",
        description=(
            "Actualiza la configuración de la plantilla: nombre, categoría, estado, "
            "fuente y coordenadas del nombre del participante. "
            "Sincroniza automáticamente el `layout_config` con los campos planos actualizados."
        ),
        request=TemplateUpdateSerializer,
        responses={200: TemplateSerializer},
    ),
    partial_update=extend_schema(
        tags=["Plantillas"],
        summary="Actualizar plantilla (parcial)",
        description="Actualiza uno o más campos de una plantilla sin enviar todos los datos.",
        responses={200: TemplateSerializer},
    ),
    destroy=extend_schema(
        tags=["Plantillas"],
        summary="Eliminar plantilla",
        description="Elimina permanentemente una plantilla y su imagen de fondo asociada. "
        "**Acción irreversible.** Solo administradores.",
        responses={
            204: OpenApiResponse(description="Plantilla eliminada correctamente."),
            404: OpenApiResponse(description="Plantilla no encontrada."),
        },
    ),
)
class TemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing certificate templates

    Endpoints:
    - GET /templates/: List all templates
    - POST /templates/: Create a new template
    - GET /templates/{id}/: Get template details
    - PUT /templates/{id}/: Update template
    - DELETE /templates/{id}/: Delete template
    - POST /templates/{id}/upload-image/: Upload background image
    - GET /templates/{id}/preview/: Get preview URL

    Only admins can create/update/delete.
    Anyone authenticated can view.
    """

    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["is_active", "category"]
    search_fields = ["name", "category"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Admin sees all templates; other users see only their own."""
        if is_operational_user(self.request):
            return Template.objects.all()
        return Template.objects.filter(created_by=self.request.user)

    def get_permissions(self):
        """Only admins can modify"""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            if is_operational_user(self.request):
                permission_classes = [permissions.IsAuthenticated]
            else:
                permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return TemplateCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return TemplateUpdateSerializer
        return TemplateSerializer

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self._sync_layout_config(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._sync_layout_config(instance)

    def _sync_layout_config(self, template):
        """Keep layout_config.participant_name in sync with the flat coord/font fields."""
        layout = dict(template.layout_config or {})
        participant_name = dict(layout.get("participant_name", {}))
        participant_name.update(
            {
                "x": template.x_coord,
                "y": template.y_coord,
                "font_size": template.font_size,
                "font_family": template.font_family,
                "color": template.font_color,
            }
        )
        layout["participant_name"] = participant_name
        template.layout_config = layout
        template.save(update_fields=["layout_config"])

    @extend_schema(
        tags=["Plantillas"],
        summary="Subir imagen de fondo de la plantilla",
        description=(
            "Sube la imagen de fondo (diseño) de la plantilla de certificado. "
            "**Formatos aceptados:** PNG o JPG únicamente.\n\n"
            "La imagen se guarda en el campo `background_image` del modelo y "
            "su URL queda disponible en `background_url`. "
            "El archivo debe enviarse en el campo `file` del formulario multipart."
        ),
        responses={
            200: OpenApiResponse(
                description="Imagen subida correctamente. Retorna success, background_image (URL) y mensaje."
            ),
            400: OpenApiResponse(description="No se proporcionó archivo o el formato no es PNG/JPG."),
            404: OpenApiResponse(description="Plantilla no encontrada."),
        },
    )
    @action(detail=True, methods=["post"], url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload background image for template"""

        template = self.get_object()

        # Get file from request - try different keys
        uploaded_file = None
        if "file" in request.FILES:
            uploaded_file = request.FILES["file"]
        elif request.FILES:
            uploaded_file = next(iter(request.FILES.values()))

        if not uploaded_file:
            return Response(
                {"error": "No se encontró archivo de imagen"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file type
        valid_types = ["image/png", "image/jpeg", "image/jpg"]
        content_type = getattr(uploaded_file, "content_type", "")
        filename = getattr(uploaded_file, "name", "")
        if content_type not in valid_types:
            logger.warning("Upload rejected: file=%s, content_type=%s", filename, content_type)
            return Response(
                {"error": "Solo se permiten archivos PNG o JPG"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info("Upload accepted: file=%s", filename)

        # Save image directly to the model field
        template.background_image = uploaded_file
        template.save()

        # Also save URL for reference
        if template.background_image:
            template.background_url = template.background_image.url
            template.save()

        return Response(
            {
                "success": True,
                "background_image": (template.background_image.url if template.background_image else None),
                "message": "Imagen subida correctamente",
            }
        )

    @extend_schema(
        tags=["Plantillas"],
        summary="Subir firma del instructor",
        description=(
            "Sube la imagen de la firma del instructor y/o guarda sus datos en el `layout_config` de la plantilla. "
            "**Formatos aceptados:** PNG o JPG.\n\n"
            "Campos del formulario multipart:\n"
            "- `signature_image` o `file`: imagen de la firma (opcional).\n"
            "- `instructor_name`: nombre del instructor que aparecerá bajo la firma (opcional).\n"
            "- `instructor_specialty`: especialidad del instructor (opcional).\n\n"
            "Si solo se envían nombre/especialidad sin imagen, se guardan igualmente en el `layout_config` "
            "para renderizarlos en texto en el PDF."
        ),
        responses={
            200: OpenApiResponse(
                description="Firma guardada correctamente. Retorna success, signature (config guardada) y mensaje."
            ),
            400: OpenApiResponse(description="Formato de imagen no válido."),
            404: OpenApiResponse(description="Plantilla no encontrada."),
        },
    )
    @action(detail=True, methods=["post"], url_path="upload-signature")
    def upload_signature(self, request, pk=None):
        """Upload instructor signature image for a template and save metadata to layout_config."""
        import pathlib

        from django.conf import settings as django_settings

        template = self.get_object()

        signature_file = request.FILES.get("signature_image") or request.FILES.get("file")
        instructor_name = request.data.get("instructor_name", "").strip()
        instructor_specialty = request.data.get("instructor_specialty", "").strip()

        sig_config = dict(template.layout_config.get("signature", {}))

        if signature_file:
            valid_types = ["image/png", "image/jpeg", "image/jpg"]
            if getattr(signature_file, "content_type", "") not in valid_types:
                return Response(
                    {"error": "Solo se permiten archivos PNG o JPG"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sig_dir = pathlib.Path(django_settings.MEDIA_ROOT) / "templates" / "signatures"
            sig_dir.mkdir(parents=True, exist_ok=True)
            suffix = pathlib.Path(signature_file.name).suffix or ".png"
            sig_filename = f"sig_{template.id}_{pk}{suffix}"
            sig_path = sig_dir / sig_filename
            with open(sig_path, "wb+") as dest:
                for chunk in signature_file.chunks():
                    dest.write(chunk)
            sig_config["image_path"] = str(sig_path)
            sig_config["image_url"] = f"/media/templates/signatures/{sig_filename}"

        if instructor_name:
            sig_config["instructor_name"] = instructor_name
        if instructor_specialty:
            sig_config["instructor_specialty"] = instructor_specialty

        layout = dict(template.layout_config)
        layout["signature"] = sig_config
        template.layout_config = layout
        template.save()

        return Response(
            {
                "success": True,
                "signature": sig_config,
                "message": "Firma guardada correctamente",
            }
        )

    @extend_schema(
        tags=["Plantillas"],
        summary="Previsualización de la plantilla",
        description=(
            "Retorna la URL de la imagen de fondo de la plantilla para previsualización, "
            "junto con el `layout_config` completo (coordenadas del nombre, configuración de firma, etc.). "
            "Usa `background_image` si existe, de lo contrario usa `preview_url`."
        ),
        responses={
            200: OpenApiResponse(
                description="Retorna preview_url (URL de la imagen) y layout_config "
                "(configuración completa del diseño)."
            ),
            404: OpenApiResponse(description="Plantilla no encontrada."),
        },
    )
    @action(detail=True, methods=["get"], url_path="preview")
    def get_preview(self, request, pk=None):
        """Get preview URL for template"""
        template = self.get_object()

        return Response(
            {
                "preview_url": (template.background_image.url if template.background_image else template.preview_url),
                "layout_config": template.layout_config,
            }
        )

    def perform_destroy(self, instance):
        instance.delete(deleted_by=self.request.user)
        log_action("template_deleted", user=self.request.user, ip_address=get_client_ip(self.request))

    @extend_schema(
        tags=["Plantillas"],
        summary="Historial de cambios de la plantilla",
        description=(
            "Retorna el historial completo de cambios de la plantilla: nombre, configuración "
            "de fuente, coordenadas, etc. "
            "Incluye quién hizo cada cambio y cuándo (fecha y hora exacta con segundos)."
        ),
        responses={200: ChangelogSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="changelog")
    def changelog(self, request, pk=None):
        instance = self.get_object()
        return Response(ChangelogSerializer(instance.history.all().order_by("-history_date"), many=True).data)

    @extend_schema(
        tags=["Plantillas"],
        summary="Restaurar plantilla eliminada",
        description="Restaura una plantilla eliminada con baja lógica. **Solo administradores.**",
        responses={
            200: OpenApiResponse(description="Plantilla restaurada correctamente."),
            404: OpenApiResponse(description="No encontrada o no está eliminada."),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="restore",
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser],
    )
    def restore(self, request, pk=None):
        try:
            instance = Template.all_objects.get(pk=pk, is_deleted=True)
        except Template.DoesNotExist:
            return Response({"error": "Plantilla no encontrada o no está eliminada"}, status=status.HTTP_404_NOT_FOUND)
        instance.restore()
        log_action("template_restored", user=request.user, ip_address=get_client_ip(request))
        return Response({"status": "success", "message": "Plantilla restaurada correctamente"})


class BulkCertificateGenerationView(APIView):
    """
    API endpoint para generar certificados masivamente desde Excel

    POST /api/certificates/generate-bulk/

    Funcionalidad:
    - Permite cargar un archivo Excel con datos de estudiantes y eventos
    - Procesa automáticamente creando/actualizando estudiantes
    - Crea inscripciones y genera certificados
    - Maneja errores de forma resiliente
    - Retorna resumen detallado del procesamiento

    Request:
    {
        "excel_file": <archivo.xlsx>,
        "dry_run": false  (opcional)
    }

    Response (200):
    {
        "processing_timestamp": "2026-04-02T...",
        "total_rows": 150,
        "successful": 148,
        "failed": 2,
        "success_rate": "98.7%",
        "errors": [
            {
                "row": 5,
                "field": "email",
                "message": "Email inválido",
                "data": {...}
            }
        ],
        "created_certificates": [1, 2, 3, ...],
        "data_preview": [...],
        "summary": "..."
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Certificados - Masivo"],
        summary="Generar certificados masivamente desde Excel",
        description=(
            "Carga un archivo Excel con datos de estudiantes y genera automáticamente sus certificados. "
            "**Solo administradores y coordinadores.**\n\n"
            "**Campos del formulario multipart requeridos:**\n"
            "- `excel_file`: archivo `.xlsx` o `.xls` con columnas: `full_name`, `email`, `document_id`.\n"
            "- `template_image`: imagen PNG/JPG que servirá como fondo del certificado.\n"
            "- `event_id`: ID del evento al que pertenecen los certificados.\n\n"
            "**Campos opcionales:**\n"
            "- `signature_image`: imagen de firma del instructor.\n"
            "- `instructor_name` / `instructor_specialty`: datos del instructor.\n"
            "- `name_x` / `name_y`: posición del nombre en el certificado (0-100%, por defecto 50/40).\n"
            "- `font_size`, `font_color`, `font_family`: configuración tipográfica.\n\n"
            "El proceso crea participantes si no existen, los inscribe al evento y genera los PDFs. "
            "Los errores por fila no detienen el procesamiento completo."
        ),
        responses={
            200: OpenApiResponse(
                description="Resumen: processing_timestamp, total_rows, successful, failed, "
                "success_rate, errors (detallados por fila) y created_certificates (lista de IDs)."
            ),
            400: OpenApiResponse(
                description="Falta excel_file, template_image o event_id; o error al procesar el archivo."
            ),
            403: OpenApiResponse(description="Solo administradores y coordinadores pueden usar esta función."),
            404: OpenApiResponse(description="Evento no encontrado."),
        },
    )
    def post(self, request):
        """Procesa un archivo Excel para generar y enviar certificados masivamente"""
        from api.permissions import is_operational_user

        if not is_operational_user(request):
            return Response(
                {"error": "Solo administradores y coordinadores pueden generar certificados en masa"},
                status=status.HTTP_403_FORBIDDEN,
            )

        excel_file = request.FILES.get("excel_file")
        template_image = request.FILES.get("template_image")
        event_id = request.data.get("event_id")

        if not excel_file:
            return Response(
                {"error": "Se requiere archivo Excel (excel_file)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not template_image:
            return Response(
                {"error": "Se requiere imagen de plantilla (template_image)"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not event_id:
            return Response(
                {"error": "Se requiere el ID del evento (event_id)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            event = Event.objects.get(id=int(event_id))
        except (Event.DoesNotExist, ValueError):
            return Response({"error": "Evento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        from procesos.services import ExcelProcessingService

        template = None
        try:
            # Creamos la plantilla ad-hoc
            template = ExcelProcessingService.create_bulk_template(event, request.user, template_image, request.data)

            file_bytes = BytesIO(excel_file.read())
            service = ExcelProcessingService(
                file_object=file_bytes,
                created_by_user=request.user,
                event=event,
                template=template,
            )
            result = service.process()
            result_dict = result.to_dict()
            logger.info(result.get_summary())
            return Response(result_dict, status=status.HTTP_200_OK)

        except Exception as e:
            if template and template.id:
                template.delete()
            return Response(
                {"error": "Error al procesar archivo Excel", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["Certificados - Masivo"],
        summary="Información del formato Excel para generación masiva",
        description=(
            "Retorna una guía completa sobre el formato requerido del archivo Excel para la "
            "generación masiva de certificados: "
            "columnas obligatorias, columnas opcionales, ejemplo de fila y notas importantes sobre el procesamiento."
        ),
        responses={
            200: OpenApiResponse(description="Guía con columnas requeridas/opcionales, ejemplo y notas del proceso.")
        },
    )
    def get(self, request):
        """
        GET /api/certificates/generate-bulk/

        Devuelve información sobre el formato esperado del Excel
        """
        return Response(
            {
                "section": "Generación de Certificados",
                "endpoint": "POST /api/certificates/generate-bulk/",
                "description": "Carga un archivo Excel para generar certificados masivamente",
                "required_columns": {
                    "full_name": "Nombre completo del estudiante",
                    "email": "Email del estudiante",
                    "document_id": "Documento de identidad (debe ser único)",
                    "event_name": "Nombre del evento (debe existir en el sistema)",
                },
                "optional_columns": {
                    "phone": "Teléfono del estudiante",
                    "institution": "Institución",
                    "certificate_template": "Plantilla de certificado (por nombre)",
                },
                "example_file": {
                    "full_name": "Juan Pérez García",
                    "email": "juan@example.com",
                    "document_id": "1234567890",
                    "event_name": "Curso de Python",
                    "phone": "+57 123 456 7890",
                },
                "notes": [
                    "El archivo debe ser en formato .xlsx o .xls",
                    "Los eventos deben crearse previamente en el sistema",
                    "Los emails deben ser válidos",
                    "Se evita duplicación automáticamente",
                    "Los errores por fila no detienen el procesamiento",
                ],
                "response_includes": {
                    "total_rows": "Total de filas procesadas",
                    "successful": "Cantidad de certificados creados exitosamente",
                    "failed": "Cantidad de errores",
                    "success_rate": "Porcentaje de éxito",
                    "errors": "Listado detallado de errores por fila",
                    "created_certificates": "IDs de certificados creados",
                },
            },
            status=status.HTTP_200_OK,
        )


class BulkCertificatePreviewView(APIView):
    """
    API endpoint para extraer datos de un Excel SIN procesar certificados

    POST /api/certificates/preview/

    Funcionalidad:
    - Lee el archivo Excel
    - Valida estructura de columnas
    - Retorna datos extraídos para edición
    - NO crea certificados

    Request:
    {
        "excel_file": <archivo.xlsx>
    }

    Response (200):
    {
        "success": true,
        "row_count": 150,
        "columns": ["full_name", "email", "document_id", "event_name"],
        "data": [
            {
                "full_name": "Juan Pérez",
                "email": "juan@example.com",
                "document_id": "1234567890",
                "event_name": "Curso Python"
            },
            ...
        ]
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Certificados - Masivo"],
        summary="Previsualizar datos del Excel (sin crear certificados)",
        description=(
            "Lee un archivo Excel y retorna los datos extraídos para que el usuario los revise y edite "
            "**antes** de generar los certificados. **No crea ni modifica ningún registro.** "
            "Solo administradores y coordinadores.\n\n"
            "El archivo debe enviarse en el campo `excel_file` (multipart/form-data). "
            "Retorna las columnas detectadas y todos los registros como lista de objetos JSON, "
            "listos para edición antes de enviarlos a `/api/certificates/process/`."
        ),
        request=ExcelBulkImportSerializer,
        examples=[
            OpenApiExample(
                "Preview de Excel",
                value={"excel_file": "(archivo .xlsx)"},
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="success, row_count (total de filas), columns (nombres de "
                "columnas) y data (lista de registros)."
            ),
            400: OpenApiResponse(
                description="Archivo no proporcionado, formato inválido o columnas requeridas faltantes."
            ),
            403: OpenApiResponse(description="Solo administradores y coordinadores pueden previsualizar archivos."),
        },
    )
    def post(self, request):
        """Extrae datos del Excel para preview"""

        from api.permissions import is_operational_user

        if not is_operational_user(request):
            return Response(
                {"error": "Solo administradores y coordinadores pueden previsualizar archivos"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ExcelBulkImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        excel_file = serializer.validated_data["excel_file"]

        try:
            # Convertir UploadedFile a BytesIO
            file_bytes = BytesIO(excel_file.read())

            # Crear servicio y extraer datos
            service = ExcelProcessingService(file_object=file_bytes, created_by_user=request.user)
            data = service.read_and_validate_structure()

            logger.info(
                "Preview: %s registros extraídos por usuario %s",
                len(data),
                request.user,
            )

            return Response(
                {
                    "success": True,
                    "row_count": len(data),
                    "columns": list(data[0].keys()) if data else [],
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        except ExcelImportError as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error en preview")
            return Response(
                {
                    "success": False,
                    "error": "Error al procesar archivo Excel",
                    "detail": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class BulkCertificateProcessView(APIView):
    """
    API endpoint para procesar datos editados y crear certificados

    POST /api/certificates/process/

    Funcionalidad:
    - Recibe array de datos (posiblemente editados)
    - Valida datos
    - Crea certificados
    - Retorna resumen con IDs creados y errores

    Request:
    {
        "data": [
            {
                "full_name": "Juan Pérez",
                "email": "juan@example.com",
                "document_id": "1234567890",
                "event_name": "Curso Python"
            },
            ...
        ]
    }

    Response (200):
    {
        "processing_timestamp": "2026-04-02T...",
        "total_rows": 150,
        "successful": 148,
        "failed": 2,
        "success_rate": "98.7%",
        "errors": [...],
        "created_certificates": [1, 2, 3, ...]
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Certificados - Masivo"],
        summary="Procesar registros editados y crear certificados",
        description=(
            "Recibe un array de registros (posiblemente editados tras la previsualización) "
            "y los procesa para crear los certificados correspondientes.\n\n"
            "**Flujo de uso:** `/api/certificates/preview/` → editar datos → `/api/certificates/process/`.\n\n"
            "El body debe contener un campo `data` con el array de registros. "
            "Cada registro debe tener al menos `full_name`, `email`, `document_id` y `event_name`. "
            "Los errores por registro no detienen el procesamiento de los demás."
        ),
        request=BulkProcessDataSerializer,
        examples=[
            OpenApiExample(
                "Procesar registros editados",
                value={
                    "data": [
                        {
                            "full_name": "Juan Pérez",
                            "email": "juan@example.com",
                            "document_id": "12345",
                            "event_name": "Curso Python",
                        },
                        {
                            "full_name": "María García",
                            "email": "maria@example.com",
                            "document_id": "67890",
                            "event_name": "Curso Python",
                        },
                    ]
                },
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Resumen: processing_timestamp, total_rows, successful, failed, "
                "success_rate, errors y created_certificates."
            ),
            400: OpenApiResponse(description="El campo `data` está ausente, no es un array o está vacío."),
            500: OpenApiResponse(description="Error inesperado durante el procesamiento."),
        },
    )
    def post(self, request):
        """Procesa datos editados y crea certificados"""

        data_list = request.data.get("data", [])

        if not isinstance(data_list, list) or len(data_list) == 0:
            return Response(
                {
                    "error": "Datos inválidos",
                    "detail": 'Se requiere un array "data" con al menos un registro',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Crear servicio y procesar datos
            service = ExcelProcessingService(file_object=None, created_by_user=request.user)

            # Procesar los registros editados
            result = service.process_records(records=data_list)

            # Log de resumen
            logger.info(
                "Procesamiento: %s/%s exitosos por usuario %s",
                result.successful,
                result.total_rows,
                request.user,
            )

            return Response(result.to_dict(), status=status.HTTP_200_OK)

        except ExcelImportError as e:
            logger.exception("Error en procesamiento")
            return Response(
                {"error": "Error al procesar registros", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.exception("Error inesperado en procesamiento")
            return Response(
                {"error": "Error inesperado al procesar registros", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EnrollmentViewSet(viewsets.ViewSet):
    """
    ViewSet for managing enrollments (event participants)

    Endpoints are accessed via event/{id}/enrollments/ actions
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            if is_operational_user(self.request):
                self.permission_classes = [permissions.IsAuthenticated]
            else:
                self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    @extend_schema(
        tags=["Inscripciones"],
        summary="Listar inscripciones de un evento",
        description=(
            "Retorna todas las inscripciones del evento especificado. "
            "Admins/coordinadores ven cualquier evento; otros usuarios solo los eventos que crearon. "
            "Incluye datos del participante, asistencia, notas y estado de envío del certificado."
        ),
        responses={200: EnrollmentSerializer(many=True)},
    )
    def list(self, request, event_pk=None):
        """List enrollments — admin sees all, coordinator sees own events' enrollments, others 403"""
        from events.models import Enrollment

        if is_admin(request):
            enrollments = Enrollment.objects.all().select_related("participant", "created_by")
        elif is_operational_user(request):
            user_events = Event.objects.filter(created_by=request.user).values_list("id", flat=True)
            enrollments = Enrollment.objects.filter(event_id__in=user_events).select_related(
                "participant", "created_by"
            )
        else:
            return Response(
                {"error": "No tienes permiso para listar inscripciones."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Inscripciones"],
        summary="Inscribir participante a un evento",
        description=(
            "Inscribe un participante existente al evento. "
            "Se debe enviar `participant_id` para identificar al participante. "
            "Campos opcionales: `attendance` (asistencia, por defecto `false`), `grade` (calificación) y `notes`.\n\n"
            "Retorna error si el participante ya está inscrito en ese evento."
        ),
        request=EnrollmentCreateSerializer,
        responses={
            201: EnrollmentSerializer,
            400: OpenApiResponse(description="Participante ya inscrito o datos inválidos."),
            404: OpenApiResponse(description="Participante o evento no encontrado."),
        },
    )
    def create(self, request, event_pk=None):
        """Enroll a participant to an event — only the event creator can enroll"""
        from events.models import Enrollment
        from participants.models import Participant

        serializer = EnrollmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        participant_id = serializer.validated_data["participant_id"]
        attendance = serializer.validated_data.get("attendance", False)
        grade = serializer.validated_data.get("grade")
        notes = serializer.validated_data.get("notes", "")

        try:
            participant = Participant.objects.get(id=participant_id)
        except Participant.DoesNotExist:
            return Response(
                {"error": "Participante no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        resolved_event_pk = event_pk or request.data.get("event_id")
        try:
            event = Event.objects.get(id=resolved_event_pk)
        except (Event.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Evento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para inscribir participantes en este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        enrollment, created = Enrollment.objects.get_or_create(
            participant=participant,
            event=event,
            defaults={
                "attendance": attendance,
                "grade": grade,
                "notes": notes,
                "created_by": request.user,
            },
        )

        if not created:
            return Response(
                {"error": "El participante ya está inscrito en este evento"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    def _get_enrollment(self, pk):
        from events.models import Enrollment

        try:
            return Enrollment.objects.get(id=pk), None
        except Enrollment.DoesNotExist:
            return None, Response({"error": "Inscripción no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Inscripciones"],
        summary="Eliminar inscripción",
        description=(
            "Elimina la inscripción de un participante de un evento. "
            "**Acción irreversible.** Si el participante tiene certificado generado, "
            "este no se elimina automáticamente."
        ),
        responses={
            204: OpenApiResponse(description="Inscripción eliminada correctamente."),
            404: OpenApiResponse(description="Inscripción no encontrada."),
        },
    )
    def destroy(self, request, event_pk=None, pk=None):
        """Remove a student from an event — only the event creator can remove enrollments"""
        enrollment, error = self._get_enrollment(pk)
        if error:
            return error
        if enrollment.event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para eliminar inscripciones de este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Inscripciones"],
        summary="Marcar asistencia de un participante",
        description=(
            "Actualiza el campo `attendance` de una inscripción para marcar si el participante asistió al evento. "
            'Solo se requiere enviar `{"attendance": true}` o `{"attendance": false}` en el body. '
            "**La asistencia debe estar en `true` para que se genere el certificado del participante.**"
        ),
        responses={
            200: EnrollmentSerializer,
            400: OpenApiResponse(description="Campo `attendance` no proporcionado."),
            404: OpenApiResponse(description="Inscripción no encontrada."),
        },
    )
    @action(detail=True, methods=["patch"])
    def attendance(self, request, event_pk=None, pk=None):
        """Mark attendance for an enrollment — only the event creator can mark attendance"""
        enrollment, error = self._get_enrollment(pk)
        if error:
            return error

        if enrollment.event.created_by != request.user:
            return Response(
                {"error": "No tienes permiso para marcar asistencia en este evento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        attendance = request.data.get("attendance")
        if attendance is None:
            return Response(
                {"error": "Campo attendance es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment.attendance = attendance
        enrollment.save()

        return Response(EnrollmentSerializer(enrollment).data)


_ERR_INVITATION_NOT_FOUND = "Invitación no encontrada"
_ERR_INVITATION_EXPIRED = "La invitación ha expirado"


class InvitationPublicView(APIView):
    """
    Public endpoints for invitation response (no auth required)
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Invitaciones"],
        summary="Obtener detalles de invitación (público)",
        description=(
            "Retorna los datos de una invitación a partir de su token único. "
            "**Endpoint público: no requiere autenticación.**\n\n"
            "Retorna: datos del evento (nombre, fecha, ubicación, descripción), email del invitado, "
            "estado de la invitación, fecha de expiración y si el participante ya está registrado en el sistema. "
            "Si la invitación ya fue respondida o expiró, retorna error."
        ),
        responses={
            200: InvitationDetailSerializer,
            400: OpenApiResponse(description="La invitación ya fue aceptada, rechazada o ha expirado."),
            404: OpenApiResponse(description="No existe ninguna invitación con ese token."),
        },
    )
    def get(self, request, token):
        """
        Get invitation details - check if student exists
        GET /api/invitations/<token>/
        """
        from django.utils import timezone

        from events.models import EventInvitation

        try:
            invitation = EventInvitation.objects.select_related("event").get(token=token)
        except EventInvitation.DoesNotExist:
            return Response({"error": _ERR_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        # Check if expired
        if invitation.status in ["accepted", "rejected"]:
            return Response(
                {"error": f"La invitación ya ha sido {invitation.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.expires_at and invitation.expires_at < timezone.now():
            invitation.status = "expired"
            invitation.save()
            return Response({"error": _ERR_INVITATION_EXPIRED}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InvitationDetailSerializer(invitation)
        return Response(serializer.data)

    @extend_schema(
        tags=["Invitaciones"],
        summary="Aceptar invitación (participante ya registrado, público)",
        description=(
            "Acepta una invitación cuando el participante **ya existe** en el sistema. "
            "**Endpoint público: no requiere autenticación.**\n\n"
            "Busca al participante por el email de la invitación. Si no existe como participante, "
            "retorna error indicando que debe registrarse primero con `/register/`.\n\n"
            "Al aceptar: crea o actualiza la inscripción del participante al evento (con `attendance=True`), "
            "crea un certificado en estado `pending` y marca la invitación como `accepted`."
        ),
        responses={
            200: OpenApiResponse(
                description="Inscripción exitosa. Retorna mensaje, nombre del evento y nombre del participante."
            ),
            400: OpenApiResponse(
                description="Invitación ya respondida, expirada, o el participante debe registrarse primero."
            ),
            404: OpenApiResponse(description="Invitación no encontrada."),
        },
    )
    def post(self, request, token):
        """
        Accept invitation (if student already exists)
        POST /api/invitations/<token>/accept/
        """
        from django.utils import timezone

        from events.models import Enrollment, EventInvitation

        try:
            invitation = EventInvitation.objects.select_related("event").get(token=token)
        except EventInvitation.DoesNotExist:
            return Response({"error": _ERR_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        # Check if already responded
        if invitation.status in ["accepted", "rejected"]:
            return Response(
                {"error": f"La invitación ya ha sido {invitation.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check expiration
        if invitation.expires_at and invitation.expires_at < timezone.now():
            invitation.status = "expired"
            invitation.save()
            return Response({"error": _ERR_INVITATION_EXPIRED}, status=status.HTTP_400_BAD_REQUEST)

        if not invitation.participant:
            from participants.models import Participant

            invitation.participant = Participant.objects.filter(email__iexact=invitation.email).first()
            if not invitation.participant:
                return Response(
                    {"error": "Debes registrarte primero"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            invitation.save()

        # Create enrollment (without invitation FK to avoid DB error)
        enrollment, created = Enrollment.objects.get_or_create(
            participant=invitation.participant,
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

        # Auto-create certificate in pending status so it appears in the list
        from certificados.models import Certificate

        Certificate.objects.get_or_create(
            participant=invitation.participant,
            event=invitation.event,
            defaults={
                "template": invitation.event.template,
                "status": "pending",
            },
        )

        invitation.status = "accepted"
        invitation.responded_at = timezone.now()
        invitation.save()

        return Response(
            {
                "message": "¡Inscripción exitosa!",
                "event": invitation.event.name,
                "participant": invitation.participant.full_name,
            }
        )


class InvitationRegisterView(APIView):
    """
    Register a new student via invitation
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["Invitaciones"],
        summary="Registrarse y aceptar invitación (nuevo participante, público)",
        description=(
            "Registra un **nuevo estudiante** en el sistema y acepta la invitación en un solo paso. "
            "**Endpoint público: no requiere autenticación.**\n\n"
            "Si ya existe un usuario con el email de la invitación, reutiliza ese usuario y solo crea el participante. "
            "Si no existe, crea tanto el usuario (con rol `participante`) como el participante.\n\n"
            "Al completarse: crea la inscripción al evento, crea certificado en estado `pending` "
            "y marca la invitación como `accepted`.\n\n"
            "**Campos requeridos:** `first_name`, `last_name`, `password` (mínimo 8 caracteres). "
            "**Opcionales:** `phone`."
        ),
        request=InvitationRegisterSerializer,
        responses={
            200: OpenApiResponse(
                description="Registro exitoso. Retorna mensaje, nombre del evento, nombre del participante y email."
            ),
            400: OpenApiResponse(description="Datos inválidos, invitación ya respondida o expirada."),
            404: OpenApiResponse(description="Invitación no encontrada."),
        },
    )
    def post(self, request, token):
        """
        Register student and accept invitation
        POST /api/invitations/<token>/register/
        Body: {
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": "1234567890",
            "password": "micontraseña"
        }
        """
        from django.contrib.auth import get_user_model
        from django.utils import timezone

        from events.models import Enrollment, EventInvitation

        try:
            invitation = EventInvitation.objects.select_related("event").get(token=token)
        except EventInvitation.DoesNotExist:
            return Response({"error": _ERR_INVITATION_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        # Check if already responded
        if invitation.status in ["accepted", "rejected"]:
            return Response(
                {"error": f"La invitación ya ha sido {invitation.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check expiration
        if invitation.expires_at and invitation.expires_at < timezone.now():
            invitation.status = "expired"
            invitation.save()
            return Response({"error": _ERR_INVITATION_EXPIRED}, status=status.HTTP_400_BAD_REQUEST)

        # Validate data
        serializer = InvitationRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        email = invitation.email.lower()

        # Check if user already exists with this email
        user_model = get_user_model()
        existing_user = user_model.objects.filter(email__iexact=email).first()

        if existing_user:
            participant, _ = Participant.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "phone": data.get("phone", ""),
                    "document_id": f"USR-{existing_user.id}",
                },
            )
        else:
            with transaction.atomic():
                user = user_model.objects.create_user(
                    email=email,
                    full_name=f"{data['first_name']} {data['last_name']}",
                    password=data["password"],
                    role="participante",
                )
                participant = Participant.objects.create(
                    email=email,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    phone=data.get("phone", ""),
                    document_id=f"PART-{user.id}",
                    created_by=invitation.created_by,
                )

        # Update invitation
        invitation.participant = participant
        invitation.status = "accepted"
        invitation.responded_at = timezone.now()
        invitation.save()

        # Create enrollment (without invitation reference to avoid FK issues)
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

        # Auto-create certificate in pending status so it appears in the list
        from certificados.models import Certificate

        Certificate.objects.get_or_create(
            participant=participant,
            event=invitation.event,
            defaults={
                "template": invitation.event.template,
                "status": "pending",
            },
        )

        return Response(
            {
                "message": "¡Registro exitoso! Ya estás inscrito en el evento.",
                "event": invitation.event.name,
                "participant": participant.full_name,
                "email": email,
            }
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Auditoría"],
        summary="Listar registros de auditoría",
        description=(
            "Retorna el log completo de todas las acciones realizadas en el sistema, "
            "ordenadas de la más reciente a la más antigua. **Solo administradores.**\n\n"
            "Acciones registradas: `user_login`, `user_login_failed`, `certificate_generated`, "
            "`certificate_delivered`, `certificate_retried`, `export_requested`, entre otras.\n\n"
            "Soporta filtrado por `action` (tipo de acción) y `user_id` (usuario que realizó la acción). "
            "Cada registro incluye: acción, usuario, certificado relacionado (si aplica), IP de origen, "
            "detalles adicionales en JSON y timestamp exacto."
        ),
        parameters=[
            OpenApiParameter(
                "action",
                OpenApiTypes.STR,
                description="Filtrar por tipo de acción (ej: `user_login`, "
                "`certificate_generated`, `certificate_delivered`).",
            ),
            OpenApiParameter(
                "user_id",
                OpenApiTypes.INT,
                description="Filtrar acciones realizadas por un usuario específico (por su ID).",
            ),
        ],
        responses={200: AuditLogSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Auditoría"],
        summary="Detalle de registro de auditoría",
        description=(
            "Retorna los datos completos de un evento de auditoría específico: "
            "acción ejecutada, usuario que la realizó, certificado relacionado, "
            "dirección IP de origen, detalles adicionales en formato JSON y timestamp exacto."
        ),
        responses={
            200: AuditLogSerializer,
            404: OpenApiResponse(description="Registro de auditoría no encontrado."),
        },
    ),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for audit logs. Admin access only.

    GET /api/audit/          — paginated list, supports ?action=&user_id=
    GET /api/audit/{id}/     — single entry
    """

    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user", "certificate").order_by("-timestamp")
        action_filter = self.request.query_params.get("action")
        user_id = self.request.query_params.get("user_id")
        if action_filter:
            qs = qs.filter(action=action_filter)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs
