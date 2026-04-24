"""
ViewSets (views) for Certificate and Delivery APIs
"""
import logging
import json
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models, transaction
from rest_framework_simplejwt.tokens import RefreshToken
from io import BytesIO

from certificados.models import Certificate, Template
from deliveries.models import DeliveryLog
from events.models import Event
from students.models import Student
from users.models import User
from instructors.models import Instructor
from procesos.services import ExcelProcessingService, BulkCertificateGeneratorService, ExcelImportError
from .serializers import (
    CertificateListSerializer,
    CertificateDetailSerializer,
    CertificateCreateSerializer,
    CertificateGenerateSerializer,
    CertificateDeliverSerializer,
    DeliveryLogSerializer,
    EventSerializer,
    StudentSerializer,
    InstructorSerializer,
    UserRegisterSerializer,
    UserLoginSerializer,
    UserAuthSerializer,
    ExcelBulkImportSerializer,
    BulkImportResultSerializer,
    EnrollmentSerializer,
    EnrollmentCreateSerializer,
    EventCertificateSerializer,
    EventParticipantWithCertificateSerializer,
    TemplateSerializer,
    TemplateCreateSerializer,
    TemplateUpdateSerializer,
    EventInvitationSerializer,
    InvitationDetailSerializer,
    InvitationRegisterSerializer,
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
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'message': 'Cuenta creada exitosamente. Por favor inicia sesión.'
            }, status=status.HTTP_201_CREATED)
        
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
    
    def post(self, request):
        serializer = UserAuthSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_staff': user.is_staff,
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    
    def post(self, request):
        from google.oauth2 import id_token
        from google.auth.transport import requests
        from django.conf import settings
        from rest_framework import serializers
        
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Validar el token de Google
            CLIENT_ID = getattr(settings, 'GOOGLE_CLIENT_ID', None)
            if not CLIENT_ID:
                logger.warning('GOOGLE_CLIENT_ID not configured')
                return Response(
                    {'error': 'Google authentication not configured'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            id_info = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                CLIENT_ID
            )
            
            email = id_info.get('email')
            full_name = id_info.get('name', '')

            if not email:
                return Response(
                    {'error': 'Email not provided by Google'},
                    status=status.HTTP_400_BAD_REQUEST
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
                logger.info('New user created via Google OAuth: %s', email)
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                    'is_new_user': is_new_user,
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error('Google token validation failed: %s', str(e))
            return Response(
                {'error': 'Invalid Google token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error('Google auth error: %s', str(e))
            return Response(
                {'error': 'Authentication failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

    def get(self, request):
        user = request.user

        return Response({
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
        }, status=status.HTTP_200_OK)


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
        Admin sees all, Participante sees only THEIR certificates
        """
        from api.permissions import is_admin
        
        if is_admin(self.request):
            return Certificate.objects.all().select_related(
                'student', 'event', 'template', 'generated_by'
            )
        
        # Participante: see only their own certificates
        if self.request.user and self.request.user.is_authenticated:
            user_email = self.request.user.email
            return Certificate.objects.filter(
                student__email=user_email
            ).select_related('student', 'event', 'template', 'generated_by')
        
        return Certificate.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return CertificateCreateSerializer
        elif self.action == 'generate':
            return CertificateGenerateSerializer
        elif self.action == 'deliver':
            return CertificateDeliverSerializer
        elif self.action == 'list':
            return CertificateListSerializer
        return CertificateDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        from api.permissions import is_admin
        
        if self.action == 'verify':
            # Public endpoint
            self.permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy', 'generate', 'deliver']:
            if is_admin(self.request):
                self.permission_classes = [permissions.IsAuthenticated]
            else:
                self.permission_classes = [permissions.IsAdminUser]
        else:
            # Reading is allowed to authenticated users
            self.permission_classes = [permissions.IsAuthenticated]
        
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
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
        template_id = request.data.get('template_id')

        try:
            if template_id:
                from certificados.models import Template
                try:
                    template = Template.objects.get(id=template_id)
                    certificate.template = template
                except Template.DoesNotExist:
                    return Response(
                        {'status': 'error', 'message': 'Plantilla no encontrada'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            certificate.generate(generated_by=request.user)

            return Response(
                {
                    'status': 'success',
                    'message': 'Certificate generated successfully',
                    'certificate': CertificateDetailSerializer(certificate).data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Failed to generate certificate: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
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
        
        method = serializer.validated_data['method']
        recipient = serializer.validated_data.get('recipient')
        
        try:
            with transaction.atomic():
                certificate.deliver(
                    method=method,
                    recipient=recipient,
                    sent_by=request.user
                )
                
                return Response(
                    {
                        'status': 'success',
                        'message': f'Certificate delivered via {method}',
                        'delivery_log': DeliveryLogSerializer(
                            certificate.last_delivery_attempt
                        ).data,
                        'certificate': CertificateDetailSerializer(certificate).data
                    },
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Failed to deliver certificate: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get delivery history for a certificate
        
        GET /certificates/{id}/history/
        """
        certificate = self.get_object()
        delivery_logs = certificate.get_delivery_history()
        
        return Response(
            {
                'certificate_id': str(certificate.id),
                'total_attempts': delivery_logs.count(),
                'deliveries': DeliveryLogSerializer(delivery_logs, many=True).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.AllowAny]
    )
    def verify(self, request):
        """
        Verify a certificate by verification code (public endpoint)
        
        GET /certificates/verify/?code=XXXX-XXXX-XXXX-XXXX
        """
        code = request.query_params.get('code')
        
        if not code:
            return Response(
                {
                    'status': 'error',
                    'message': 'Verification code is required (code query parameter)'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            certificate = Certificate.objects.get(verification_code=code)
            
            # Check if expired
            if certificate.is_expired():
                return Response(
                    {
                        'status': 'error',
                        'message': 'Certificate has expired',
                        'certificate': CertificateDetailSerializer(certificate).data
                    },
                    status=status.HTTP_410_GONE
                )
            
            return Response(
                {
                    'status': 'success',
                    'message': 'Certificate verified successfully',
                    'certificate': CertificateDetailSerializer(certificate).data
                },
                status=status.HTTP_200_OK
            )
        
        except Certificate.DoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'message': 'Certificate not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )


class DeliveryLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing delivery logs (read-only)
    
    Endpoints:
    - GET /deliveries/: List all delivery logs (paginated)
    - GET /deliveries/{id}/: Retrieve a delivery log
    """
    queryset = DeliveryLog.objects.all().select_related(
        'certificate', 'sent_by'
    ).order_by('-sent_at')
    serializer_class = DeliveryLogSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter by certificate if cert_id query param provided"""
        queryset = super().get_queryset()
        
        cert_id = self.request.query_params.get('certificate_id')
        if cert_id:
            queryset = queryset.filter(certificate__id=cert_id)
        
        return queryset


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
    queryset = Event.objects.select_related('category', 'created_by').order_by('-event_date')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'category']
    search_fields = ['name', 'description']
    ordering_fields = ['event_date', 'created_at', 'name']
    ordering = ['-event_date']
    
    def get_queryset(self):
        """Admin sees all events, Participante sees only their enrolled events"""
        from api.permissions import is_admin
        from events.models import Enrollment
        
        queryset = super().get_queryset()
        
        # If admin, show all events
        if is_admin(self.request):
            return queryset
        
        # If participante, show only events they are enrolled in
        if self.request.user and self.request.user.is_authenticated:
            enrolled_event_ids = Enrollment.objects.filter(
                student__email=self.request.user.email
            ).values_list('event_id', flat=True)
            return queryset.filter(id__in=enrolled_event_ids)
        
        return queryset

    def get_permissions(self):
        """Events can be viewed by anyone authenticated; only admins can modify"""
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Auto-assign created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'], url_path='participants')
    def participants(self, request, pk=None):
        """
        Get all participants of an event with their certificate status
        GET /events/{id}/participants/
        Accessible by all authenticated users (admin and editor)
        """
        from events.models import Enrollment
        
        event = self.get_object()
        enrollments = Enrollment.objects.filter(event=event).select_related('student')
        
        participants = []
        for enrollment in enrollments:
            certificate = Certificate.objects.filter(student=enrollment.student, event=event).first()
            
            participants.append({
                'enrollment_id': enrollment.id,
                'student_id': enrollment.student.id,
                'student_name': f"{enrollment.student.first_name} {enrollment.student.last_name}",
                'student_email': enrollment.student.email,
                'student_phone': enrollment.student.phone or '',
                'attendance': enrollment.attendance,
                'certificate_id': certificate.id if certificate else None,
                'certificate_status': certificate.status if certificate else None,
                'certificate_status_display': certificate.get_status_display() if certificate else None,
                'verification_code': certificate.verification_code if certificate else None,
                'has_certificate': certificate is not None
            })
        
        return Response(participants)
    
    @action(detail=True, methods=['post'], url_path='enroll')
    def enroll(self, request, pk=None):
        """
        Enroll a student to this event
        POST /events/{id}/enroll/
        Body: {"student_id": 1} OR {"student_email": "email@example.com"}
        Admin only
        """
        from events.models import Enrollment
        from students.models import Student
        from api.permissions import is_admin
        
        if not is_admin(request):
            return Response(
                {'error': 'Solo administradores pueden inscribir participantes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        event = self.get_object()
        student_id = request.data.get('student_id')
        student_email = request.data.get('student_email')
        
        # Find student by id or email
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Estudiante no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif student_email:
            # Generate unique document_id for new student
            import uuid
            doc_id = f"EST-{uuid.uuid4().hex[:8].upper()}"
            student, created = Student.objects.get_or_create(
                email=student_email,
                defaults={
                    'document_id': doc_id,
                    'first_name': student_email.split('@')[0],
                    'last_name': '',
                    'phone': '',
                    'is_active': True,
                }
            )
        else:
            return Response(
                {'error': 'student_id o student_email es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            event=event
        )
        
        if not created:
            return Response(
                {'error': 'El estudiante ya está inscritos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='certificates/generate')
    def generate_certificates(self, request, pk=None):
        """
        Generate certificates for event participants (only those with attendance=True)
        POST /events/{id}/certificates/generate/
        Body: {"student_ids": [1, 2, 3]} (optional, if empty generates for all with attendance)
        Admin only
        """
        from api.permissions import is_admin
        
        if not is_admin(request):
            return Response(
                {'error': 'Solo administradores pueden generar certificados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from events.models import Enrollment
        
        event = self.get_object()
        student_ids = request.data.get('student_ids', [])
        
        enrollments = Enrollment.objects.filter(event=event).select_related('student')
        if student_ids:
            enrollments = enrollments.filter(student_id__in=student_ids)
        
        results = {
            'created': [],
            'already_exists': [],
            'errors': []
        }
        
        for enrollment in enrollments:
            try:
                cert, created = Certificate.objects.get_or_create(
                    student=enrollment.student,
                    event=event,
                    defaults={
                        'status': 'pending',
                        'generated_by': request.user,
                        'template': event.template
                    }
                )
                
                # If already exists with pending status, generate it now
                if not created and cert.status == 'pending':
                    cert.generate(generated_by=request.user, skip_attendance_check=True)
                    results['created'].append({
                        'student_id': enrollment.student.id,
                        'student_name': enrollment.student.full_name,
                        'certificate_id': cert.id,
                        'status': cert.status
                    })
                elif created:
                    cert.generate(generated_by=request.user, skip_attendance_check=True)
                    results['created'].append({
                        'student_id': enrollment.student.id,
                        'student_name': enrollment.student.full_name,
                        'certificate_id': cert.id,
                        'status': cert.status
                    })
                else:
                    results['already_exists'].append({
                        'student_id': enrollment.student.id,
                        'student_name': enrollment.student.full_name,
                        'certificate_id': cert.id,
                        'status': cert.status
                    })
            except Exception as e:
                results['errors'].append({
                    'student_id': enrollment.student.id,
                    'student_name': enrollment.student.full_name,
                    'error': str(e)
                })
        
        return Response({
            'event_id': event.id,
            'event_name': event.name,
            'total_enrollments': enrollments.count(),
            'created': len(results['created']),
            'already_exists': len(results['already_exists']),
            'errors': len(results['errors']),
            'results': results
        })
    
    @action(detail=True, methods=['post'], url_path='certificates/send')
    def send_certificates(self, request, pk=None):
        """
        Send certificates to event participants
        POST /events/{id}/certificates/send/
        Body: {
            "method": "email|whatsapp|link",
            "student_ids": [1, 2, 3] (optional, if empty sends to all with certificates)
        }
        Admin only
        """
        from api.permissions import is_admin
        
        if not is_admin(request):
            return Response(
                {'error': 'Solo administradores pueden enviar certificados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from events.models import Enrollment
        
        event = self.get_object()
        method = request.data.get('method', 'email')
        student_ids = request.data.get('student_ids', [])
        
        certificates = Certificate.objects.filter(event=event, status__in=['generated', 'sent', 'pending']).select_related('student')
        if student_ids:
            certificates = certificates.filter(student_id__in=student_ids)
        
        results = {
            'sent': [],
            'failed': [],
            'created_and_sent': []
        }
        
        for cert in certificates:
            try:
                # Generate if not generated
                if cert.status == 'pending':
                    cert.generate(generated_by=request.user)
                
                # Deliver
                delivery_log = cert.deliver(method=method, sent_by=request.user)

                if delivery_log.status == 'success':
                    results['sent'].append({
                        'certificate_id': cert.id,
                        'student_name': cert.student.full_name,
                        'recipient': cert.student.email,
                    })
                else:
                    results['failed'].append({
                        'certificate_id': cert.id,
                        'student_name': cert.student.full_name,
                        'error': delivery_log.error_message or 'Error al enviar',
                    })
            except Exception as e:
                results['failed'].append({
                    'certificate_id': cert.id,
                    'student_name': cert.student.full_name,
                    'error': str(e)
                })
        
        return Response({
            'event_id': event.id,
            'event_name': event.name,
            'method': method,
            'total_sent': len(results['sent']),
            'total_failed': len(results['failed']),
            'results': results
        })
    
    @action(detail=True, methods=['get'], url_path='deliveries')
    def event_deliveries(self, request, pk=None):
        """
        Get all delivery logs for an event's certificates
        GET /events/{id}/deliveries/
        """
        event = self.get_object()
        certificates = Certificate.objects.filter(event=event)
        
        deliveries = DeliveryLog.objects.filter(
            certificate__in=certificates
        ).select_related('certificate', 'sent_by').order_by('-sent_at')
        
        serializer = DeliveryLogSerializer(deliveries, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='stats')
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
        generated_certificates = certificates.filter(status='generated').count()
        sent_certificates = certificates.filter(status='sent').count()
        pending_certificates = certificates.filter(status='pending').count()
        failed_certificates = certificates.filter(status='failed').count()
        
        return Response({
            'event_id': event.id,
            'event_name': event.name,
            'total_enrollments': total_enrollments,
            'attendees': attendees,
            'absent': total_enrollments - attendees,
            'total_certificates': total_certificates,
            'generated_certificates': generated_certificates,
            'sent_certificates': sent_certificates,
            'pending_certificates': pending_certificates,
            'failed_certificates': failed_certificates
        })
    
    @action(detail=True, methods=['get'], url_path='invitations')
    def invitations(self, request, pk=None):
        """
        Get all invitations for an event
        GET /events/{id}/invitations/
        """
        from events.models import EventInvitation
        
        event = self.get_object()
        invitations = EventInvitation.objects.filter(event=event).select_related('student')
        
        serializer = EventInvitationSerializer(invitations, many=True)
        return Response(serializer.data)
    
    @staticmethod
    def _parse_emails_from_file(file):
        """Extract emails from an uploaded CSV or Excel file. Returns (emails, error_msg)."""
        import pandas as pd
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            email_col = next((col for col in df.columns if 'email' in col.lower()), None)
            if not email_col:
                return [], 'No se encontró columna de email en el archivo'
            return df[email_col].dropna().tolist(), None
        except Exception as e:
            return [], f'Error leyendo archivo: {str(e)}'

    @staticmethod
    def _parse_emails_from_json(emails_json):
        """Extract emails from a JSON value. Returns list (empty on error)."""
        try:
            if isinstance(emails_json, str):
                emails_json = json.loads(emails_json)
            return list(emails_json) if isinstance(emails_json, list) else []
        except ValueError:
            logger.warning('Invalid JSON format in emails field')
            return []

    @staticmethod
    def _send_invitation_email(invitation, event, frontend_url, expires_days, settings):
        """Send an invitation email. Returns error string, or None on success."""
        from django.core.mail import send_mail
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
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invitation.email], fail_silently=False)
            return None
        except Exception as e:
            return f'Error enviando a {invitation.email}: {str(e)}'

    @action(detail=True, methods=['post'], url_path='invitations/send')
    def send_invitations(self, request, pk=None):
        """
        Send invitations from Excel/CSV file or email list
        POST /events/{id}/invitations/send/
        Body (form-data):
        - file: Excel/CSV file (optional)
        - emails: JSON array of emails (optional, e.g., ["email1@test.com", "email2@test.com"])
        """
        from events.models import EventInvitation
        from django.utils import timezone
        from django.conf import settings
        import uuid
        from datetime import timedelta

        event = self.get_object()
        emails = []

        if 'file' in request.FILES:
            file_emails, file_error = self._parse_emails_from_file(request.FILES['file'])
            if file_error:
                return Response({'error': file_error}, status=status.HTTP_400_BAD_REQUEST)
            emails = file_emails

        if 'emails' in request.data:
            emails.extend(self._parse_emails_from_json(request.data.get('emails')))

        if not emails:
            return Response(
                {'error': 'No se encontraron emails para enviar invitaciones'},
                status=status.HTTP_400_BAD_REQUEST
            )

        expires_days = 7
        expires_at = timezone.now() + timedelta(days=expires_days)
        created = 0
        errors = []
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

        for email in emails:
            email = str(email).strip().lower()
            if not email or '@' not in email:
                errors.append(f'Email inválido: {email}')
                continue

            if EventInvitation.objects.filter(event=event, email=email).exists():
                errors.append(f'Ya existe invitación para: {email}')
                continue

            student = Student.objects.filter(email__iexact=email).first()
            invitation = EventInvitation.objects.create(
                event=event,
                student=student,
                email=email,
                token=uuid.uuid4(),
                status='pending',
                expires_at=expires_at,
                created_by=request.user
            )

            send_error = self._send_invitation_email(invitation, event, frontend_url, expires_days, settings)
            if send_error:
                errors.append(send_error)
            else:
                invitation.status = 'sent'
                invitation.sent_at = timezone.now()
                invitation.save()

            created += 1

        return Response({
            'total': len(emails),
            'created': created,
            'errors': errors
        })
    
    @action(detail=True, methods=['post'], url_path='invitations/send-all')
    def send_all_invitations(self, request, pk=None):
        """
        Send pending invitations for an event
        POST /events/{id}/invitations/send-all/
        """
        from events.models import EventInvitation
        from django.utils import timezone
        from django.conf import settings
        import uuid
        from datetime import timedelta

        event = self.get_object()
        pending = EventInvitation.objects.filter(event=event, status='pending')

        if not pending.exists():
            return Response(
                {'message': 'No hay invitaciones pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        expires_at = timezone.now() + timedelta(days=7)
        sent = 0
        errors = []

        for invitation in pending:
            invitation.expires_at = expires_at
            if not invitation.student:
                invitation.student = Student.objects.filter(email__iexact=invitation.email).first()
            if not invitation.token:
                invitation.token = uuid.uuid4()

            send_error = self._send_invitation_email(invitation, event, frontend_url, 7, settings)
            if send_error:
                errors.append(send_error)
            else:
                invitation.status = 'sent'
                invitation.sent_at = timezone.now()
                invitation.save()
                sent += 1

        return Response({'sent': sent, 'errors': errors})
    
    @action(detail=True, methods=['post'], url_path='finalize')
    def finalize_event(self, request, pk=None):
        """
        Finalize event and optionally send certificates
        POST /events/{id}/finalize/
        Body: {"send_certificates": true/false}
        """
        from events.models import Enrollment
        from django.utils import timezone

        event = self.get_object()

        if event.status == 'finished':
            return Response(
                {'error': 'El evento ya está finalizado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        send_certificates = request.data.get('send_certificates', False)
        
        # Update event status
        event.status = 'finished'
        event.save()
        
        result = {
            'event_id': event.id,
            'status': 'finished',
            'certificates_sent': 0
        }
        
        # Send certificates if requested
        if send_certificates:
            enrollments = Enrollment.objects.filter(event=event, attendance=True)

            for enrollment in enrollments:
                # Get or create certificate for this student
                certificate, _ = Certificate.objects.get_or_create(
                    student=enrollment.student,
                    event=event,
                    defaults={
                        'template': event.template,
                        'status': 'pending',
                    }
                )

                try:
                    # Generate if not already generated
                    if certificate.status == 'pending':
                        certificate.generate(generated_by=request.user)

                    # Send
                    delivery_log = certificate.deliver(method='email', sent_by=request.user)

                    if delivery_log.status == 'success':
                        enrollment.certificate_sent = True
                        enrollment.certificate_sent_at = timezone.now()
                        enrollment.certificate_sent_method = 'email'
                        enrollment.save()
                        result['certificates_sent'] += 1
                    else:
                        logger.error('Failed to send certificate %s: %s', certificate.id, delivery_log.error_message)
                except Exception as e:
                    logger.error('Error processing certificate %s: %s', certificate.id, str(e))

        return Response(result)


class StudentsViewSet(viewsets.ModelViewSet):
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
    queryset = Student.objects.all().order_by('first_name', 'last_name')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['first_name', 'last_name', 'email', 'document_id']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['first_name', 'last_name']
    
    def get_queryset(self):
        """Filter students by created_by or user's enrollments for non-admin users"""
        from events.models import Enrollment
        from api.permissions import is_admin
        queryset = super().get_queryset()
        
        if not is_admin(self.request):
            # Show students created by user OR students enrolled in user's events
            user_events = Event.objects.filter(created_by=self.request.user).values_list('id', flat=True)
            queryset = queryset.filter(
                models.Q(created_by=self.request.user) |
                models.Q(enrollments__event_id__in=user_events)
            ).distinct()
        
        return queryset
    
    def get_permissions(self):
        """Only admins can modify"""
        from api.permissions import is_admin
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            if is_admin(self.request):
                permission_classes = [permissions.IsAuthenticated]
            else:
                permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Auto-assign created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser]
    )
    def import_students(self, request):
        """
        Bulk import students from Excel/CSV file
        
        Expected form data:
        - file: Excel file (.xlsx) or CSV file with columns:
          document_id, first_name, last_name, email, phone (optional)
        
        Returns:
        {
            'total_rows': int,
            'imported': int,
            'errors': [
                {'row': int, 'error': str}
            ]
        }
        """
        import pandas as pd
        from django.db import IntegrityError
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        imported = 0
        errors = []
        
        try:
            # Read Excel or CSV file
            if file.name.endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file)
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    _, created = Student.objects.get_or_create(
                        document_id=row.get('document_id'),
                        defaults={
                            'first_name': row.get('first_name', ''),
                            'last_name': row.get('last_name', ''),
                            'email': row.get('email', ''),
                            'phone': row.get('phone', ''),
                        }
                    )
                    if created:
                        imported += 1
                except IntegrityError as e:
                    errors.append({
                        'row': idx + 2,  # +2 because of header and 0-indexing
                        'error': f'Duplicate email or document_id: {str(e)}'
                    })
                except Exception as e:
                    errors.append({
                        'row': idx + 2,
                        'error': str(e)
                    })
            
            return Response({
                'total_rows': len(df),
                'imported': imported,
                'errors': errors
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to process file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
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
    queryset = Instructor.objects.all().order_by('full_name')
    serializer_class = InstructorSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['full_name', 'email', 'specialty']
    ordering_fields = ['full_name', 'created_at']
    ordering = ['full_name']
    
    def get_queryset(self):
        """Filter instructors by created_by for non-admin users"""
        from api.permissions import is_admin
        queryset = super().get_queryset()
        
        if not is_admin(self.request):
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset
    
    def get_permissions(self):
        """Only admins can modify"""
        from api.permissions import is_admin
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            if is_admin(self.request):
                permission_classes = [permissions.IsAuthenticated]
            else:
                permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Auto-assign created_by to current user"""
        serializer.save(created_by=self.request.user)


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
    filterset_fields = ['is_active', 'category']
    search_fields = ['name', 'category']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter templates based on user - only see own templates"""
        user = self.request.user
        return Template.objects.filter(created_by=user)
    
    def get_permissions(self):
        """Only admins can modify"""
        from api.permissions import is_admin
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            if is_admin(self.request):
                permission_classes = [permissions.IsAuthenticated]
            else:
                permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TemplateCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TemplateUpdateSerializer
        return TemplateSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload background image for template"""
        
        template = self.get_object()
        
        # Get file from request - try different keys
        uploaded_file = None
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
        elif request.FILES:
            uploaded_file = list(request.FILES.values())[0]
        
        if not uploaded_file:
            return Response(
                {'error': 'No se encontró archivo de imagen'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        valid_types = ['image/png', 'image/jpeg', 'image/jpg']
        content_type = getattr(uploaded_file, 'content_type', '')
        filename = getattr(uploaded_file, 'name', '')
        if content_type not in valid_types:
            logger.warning('Upload rejected: file=%s, content_type=%s', filename, content_type)
            return Response(
                {'error': 'Solo se permiten archivos PNG o JPG'},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info('Upload accepted: file=%s', filename)

        # Save image directly to the model field
        template.background_image = uploaded_file
        template.save()

        # Also save URL for reference
        if template.background_image:
            template.background_url = template.background_image.url
            template.save()

        return Response({
            'success': True,
            'background_image': template.background_image.url if template.background_image else None,
            'message': 'Imagen subida correctamente'
        })
    
    @action(detail=True, methods=['get'], url_path='preview')
    def get_preview(self, request, pk=None):
        """Get preview URL for template"""
        template = self.get_object()
        
        return Response({
            'preview_url': template.background_image.url if template.background_image else template.preview_url,
            'layout_config': template.layout_config
        })


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
    
    def post(self, request):
        """Procesa un archivo Excel para generar y enviar certificados masivamente"""
        from api.permissions import is_admin
        from django.utils import timezone as tz

        if not is_admin(request):
            return Response(
                {'error': 'Solo administradores pueden generar certificados en masa'},
                status=status.HTTP_403_FORBIDDEN
            )

        excel_file = request.FILES.get('excel_file')
        template_image = request.FILES.get('template_image')
        event_id = request.data.get('event_id')

        if not excel_file:
            return Response({'error': 'Se requiere archivo Excel (excel_file)'}, status=status.HTTP_400_BAD_REQUEST)
        if not template_image:
            return Response({'error': 'Se requiere imagen de plantilla (template_image)'}, status=status.HTTP_400_BAD_REQUEST)
        if not event_id:
            return Response({'error': 'Se requiere el ID del evento (event_id)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=int(event_id))
        except (Event.DoesNotExist, ValueError):
            return Response({'error': 'Evento no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Coordenadas del nombre (porcentaje 0-100, y desde arriba)
        name_x = float(request.data.get('name_x', 50))
        name_y = float(request.data.get('name_y', 40))
        font_size = int(request.data.get('font_size', 28))
        font_color = request.data.get('font_color', '#000000')
        font_family = request.data.get('font_family', 'Helvetica')

        # Convertir porcentaje a pulgadas para layout_config
        # A4 horizontal: 841.89 x 595.28 pts / 72 pts/inch
        x_inch = name_x / 100 * 841.89 / 72
        y_inch = (1 - name_y / 100) * 595.28 / 72

        layout_config = {
            'student_name': {
                'x': x_inch,
                'y': y_inch,
                'font_size': font_size,
                'font_family': font_family,
                'color': font_color,
                'centered': True,
            }
        }

        template = Template.objects.create(
            name=f'Bulk - {event.name} - {tz.now().strftime("%Y%m%d%H%M%S")}',
            created_by=request.user,
            background_image=template_image,
            layout_config=layout_config,
            font_color=font_color,
            font_family=font_family,
            font_size=font_size,
            x_coord=x_inch,
            y_coord=y_inch,
            is_active=False,
        )

        try:
            file_bytes = BytesIO(excel_file.read())
            from procesos.services import ExcelProcessingService
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
            template.delete()
            return Response(
                {'error': 'Error al procesar archivo Excel', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get(self, request):
        """
        GET /api/certificates/generate-bulk/
        
        Devuelve información sobre el formato esperado del Excel
        """
        return Response({
            'section': 'Generación de Certificados',
            'endpoint': 'POST /api/certificates/generate-bulk/',
            'description': 'Carga un archivo Excel para generar certificados masivamente',
            'required_columns': {
                'full_name': 'Nombre completo del estudiante',
                'email': 'Email del estudiante',
                'document_id': 'Documento de identidad (debe ser único)',
                'event_name': 'Nombre del evento (debe existir en el sistema)',
            },
            'optional_columns': {
                'phone': 'Teléfono del estudiante',
                'institution': 'Institución',
                'certificate_template': 'Plantilla de certificado (por nombre)',
            },
            'example_file': {
                'full_name': 'Juan Pérez García',
                'email': 'juan@example.com',
                'document_id': '1234567890',
                'event_name': 'Curso de Python',
                'phone': '+57 123 456 7890'
            },
            'notes': [
                'El archivo debe ser en formato .xlsx o .xls',
                'Los eventos deben crearse previamente en el sistema',
                'Los emails deben ser válidos',
                'Se evita duplicación automáticamente',
                'Los errores por fila no detienen el procesamiento',
            ],
            'response_includes': {
                'total_rows': 'Total de filas procesadas',
                'successful': 'Cantidad de certificados creados exitosamente',
                'failed': 'Cantidad de errores',
                'success_rate': 'Porcentaje de éxito',
                'errors': 'Listado detallado de errores por fila',
                'created_certificates': 'IDs de certificados creados',
            }
        }, status=status.HTTP_200_OK)


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
    
    def post(self, request):
        """Extrae datos del Excel para preview"""
        
        from api.permissions import is_admin
        
        if not is_admin(request):
            return Response(
                {'error': 'Solo administradores pueden previsualizar archivos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ExcelBulkImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        excel_file = serializer.validated_data['excel_file']
        
        try:
            # Convertir UploadedFile a BytesIO
            file_bytes = BytesIO(excel_file.read())
            
            # Crear servicio y extraer datos
            service = ExcelProcessingService(file_object=file_bytes, created_by_user=request.user)
            data = service.read_and_validate_structure()
            
            logger.info("Preview: %s registros extraídos por usuario %s", len(data), request.user)
            
            return Response(
                {
                    'success': True,
                    'row_count': len(data),
                    'columns': list(data[0].keys()) if data else [],
                    'data': data
                },
                status=status.HTTP_200_OK
            )
            
        except ExcelImportError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Error en preview: %s", str(e))
            return Response(
                {
                    'success': False,
                    'error': 'Error al procesar archivo Excel',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
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
    
    def post(self, request):
        """Procesa datos editados y crea certificados"""
        
        data_list = request.data.get('data', [])
        
        if not isinstance(data_list, list) or len(data_list) == 0:
            return Response(
                {
                    'error': 'Datos inválidos',
                    'detail': 'Se requiere un array "data" con al menos un registro'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Crear servicio y procesar datos
            service = ExcelProcessingService(file_object=None, created_by_user=request.user)
            
            # Procesar los registros editados
            result = service.process_records(records=data_list)
            
            # Log de resumen
            logger.info("Procesamiento: %s/%s exitosos por usuario %s", result.successful, result.total_rows, request.user)
            
            return Response(
                result.to_dict(),
                status=status.HTTP_200_OK
            )
            
        except ExcelImportError as e:
            logger.error("Error en procesamiento: %s", str(e))
            return Response(
                {
                    'error': 'Error al procesar registros',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Error inesperado en procesamiento: %s", str(e))
            return Response(
                {
                    'error': 'Error inesperado al procesar registros',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnrollmentViewSet(viewsets.ViewSet):
    """
    ViewSet for managing enrollments (event participants)
    
    Endpoints are accessed via event/{id}/enrollments/ actions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        from api.permissions import is_admin
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            if is_admin(self.request):
                self.permission_classes = [permissions.IsAuthenticated]
            else:
                self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()
    
    def list(self, request, event_pk=None):
        """List all enrollments for an event"""
        from events.models import Enrollment
        from api.permissions import is_admin
        
        # Verify user has access to this event
        if not is_admin(request):
            event = Event.objects.filter(id=event_pk, created_by=request.user).first()
            if not event:
                return Response(
                    {'error': 'No tienes acceso a este evento'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        enrollments = Enrollment.objects.filter(event_id=event_pk).select_related('student', 'created_by')
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    def create(self, request, event_pk=None):
        """Enroll a student to an event"""
        from events.models import Enrollment
        from students.models import Student
        
        serializer = EnrollmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        student_id = serializer.validated_data['student_id']
        attendance = serializer.validated_data.get('attendance', False)
        grade = serializer.validated_data.get('grade')
        notes = serializer.validated_data.get('notes', '')
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Estudiante no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        resolved_event_pk = event_pk or request.data.get('event_id')
        try:
            event = Event.objects.get(id=resolved_event_pk)
        except (Event.DoesNotExist, ValueError, TypeError):
            return Response(
                {'error': 'Evento no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            event=event,
            defaults={
                'attendance': attendance,
                'grade': grade,
                'notes': notes,
                'created_by': request.user
            }
        )
        
        if not created:
            return Response(
                {'error': 'El estudiante ya está inscrito en este evento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED
        )
    
    def _get_enrollment(self, pk):
        from events.models import Enrollment
        try:
            return Enrollment.objects.get(id=pk), None
        except Enrollment.DoesNotExist:
            return None, Response(
                {'error': 'Inscripción no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, event_pk=None, pk=None):
        """Remove a student from an event"""
        enrollment, error = self._get_enrollment(pk)
        if error:
            return error
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'])
    def attendance(self, request, event_pk=None, pk=None):
        """Mark attendance for an enrollment"""
        enrollment, error = self._get_enrollment(pk)
        if error:
            return error
        
        attendance = request.data.get('attendance')
        if attendance is None:
            return Response(
                {'error': 'Campo attendance es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment.attendance = attendance
        enrollment.save()
        
        return Response(EnrollmentSerializer(enrollment).data)


_ERR_INVITATION_NOT_FOUND = 'Invitación no encontrada'
_ERR_INVITATION_EXPIRED = 'La invitación ha expirado'


class InvitationPublicView(APIView):
    """
    Public endpoints for invitation response (no auth required)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """
        Get invitation details - check if student exists
        GET /api/invitations/<token>/
        """
        from events.models import EventInvitation
        from django.utils import timezone
        
        try:
            invitation = EventInvitation.objects.select_related('event').get(token=token)
        except EventInvitation.DoesNotExist:
            return Response(
                {'error': _ERR_INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if expired
        if invitation.status in ['accepted', 'rejected']:
            return Response(
                {'error': f'La invitación ya ha sido {invitation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.expires_at and invitation.expires_at < timezone.now():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': _ERR_INVITATION_EXPIRED},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = InvitationDetailSerializer(invitation)
        return Response(serializer.data)
    
    def post(self, request, token):
        """
        Accept invitation (if student already exists)
        POST /api/invitations/<token>/accept/
        """
        from events.models import EventInvitation, Enrollment
        from django.utils import timezone
        
        try:
            invitation = EventInvitation.objects.select_related('event').get(token=token)
        except EventInvitation.DoesNotExist:
            return Response(
                {'error': _ERR_INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already responded
        if invitation.status in ['accepted', 'rejected']:
            return Response(
                {'error': f'La invitación ya ha sido {invitation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check expiration
        if invitation.expires_at and invitation.expires_at < timezone.now():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': _ERR_INVITATION_EXPIRED},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Must have existing student to accept directly
        if not invitation.student:
            # Check if a student exists with this email
            from students.models import Student
            invitation.student = Student.objects.filter(email__iexact=invitation.email).first()
            if not invitation.student:
                return Response(
                    {'error': 'Debes registrarte primero'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            invitation.save()
        
        # Create enrollment (without invitation FK to avoid DB error)
        enrollment, created = Enrollment.objects.get_or_create(
            student=invitation.student,
            event=invitation.event,
            defaults={
                'created_by': invitation.created_by,
                'invitation_sent': True,
                'attendance': True,
            }
        )
        if not created:
            enrollment.attendance = True
            enrollment.save()

        # Auto-create certificate in pending status so it appears in the list
        from certificados.models import Certificate
        Certificate.objects.get_or_create(
            student=invitation.student,
            event=invitation.event,
            defaults={
                'template': invitation.event.template,
                'status': 'pending',
            }
        )

        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()

        return Response({
            'message': '¡Inscripción exitosa!',
            'event': invitation.event.name,
            'student': invitation.student.full_name
        })


class InvitationRegisterView(APIView):
    """
    Register a new student via invitation
    """
    permission_classes = [permissions.AllowAny]
    
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
        from events.models import EventInvitation, Enrollment
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        
        try:
            invitation = EventInvitation.objects.select_related('event').get(token=token)
        except EventInvitation.DoesNotExist:
            return Response(
                {'error': _ERR_INVITATION_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already responded
        if invitation.status in ['accepted', 'rejected']:
            return Response(
                {'error': f'La invitación ya ha sido {invitation.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check expiration
        if invitation.expires_at and invitation.expires_at < timezone.now():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': _ERR_INVITATION_EXPIRED},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
            # Link to existing user as student
            student, _ = Student.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data.get('phone', ''),
                    'document_id': f"USR-{existing_user.id}"
                }
            )
        else:
            # Create new user and student
            with transaction.atomic():
                # Create user account
                user = user_model.objects.create_user(
                    email=email,
                    full_name=f"{data['first_name']} {data['last_name']}",
                    password=data['password'],
                    role='participante'
                )
                
                # Create student
                student = Student.objects.create(
                    email=email,
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    phone=data.get('phone', ''),
                    document_id=f"STD-{user.id}",
                    created_by=invitation.created_by
                )
        
        # Update invitation
        invitation.student = student
        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Create enrollment (without invitation reference to avoid FK issues)
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            event=invitation.event,
            defaults={
                'created_by': invitation.created_by,
                'invitation_sent': True,
                'attendance': True,
            }
        )
        if not created:
            enrollment.attendance = True
            enrollment.save()

        # Auto-create certificate in pending status so it appears in the list
        from certificados.models import Certificate
        Certificate.objects.get_or_create(
            student=student,
            event=invitation.event,
            defaults={
                'template': invitation.event.template,
                'status': 'pending',
            }
        )

        return Response({
            'message': '¡Registro exitoso! Ya estás inscrito en el evento.',
            'event': invitation.event.name,
            'student': student.full_name,
            'email': email
        })

