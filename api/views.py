"""
ViewSets (views) for Certificate and Delivery APIs
"""
import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from io import BytesIO

from certificados.models import Certificate
from deliveries.models import DeliveryLog
from events.models import Event
from students.models import Student
from users.models import User
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
    UserRegisterSerializer,
    UserLoginSerializer,
    UserAuthSerializer,
    ExcelBulkImportSerializer,
    BulkImportResultSerializer,
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
                    'first_name': user.full_name,  # El frontend espera first_name
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        """
        if self.request.user.is_staff:
            return Certificate.objects.all().select_related(
                'student', 'event', 'template', 'generated_by'
            )
        # Non-admin users can only see their own certificates
        return Certificate.objects.filter(
            student__user=self.request.user
        ).select_related('student', 'event', 'template', 'generated_by')
    
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
        if self.action == 'verify':
            # Public endpoint
            self.permission_classes = [permissions.AllowAny]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Writing requires staff
            self.permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        elif self.action in ['generate', 'deliver']:
            # Custom actions require staff
            self.permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            template_id = serializer.validated_data.get('template_id')
            if template_id:
                from certificados.models import Template
                template = Template.objects.get(id=template_id)
                certificate.template = template
            
            certificate.generate()
            
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
    
    def get_permissions(self):
        """Events can be viewed by anyone authenticated; only admins can modify"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Auto-assign created_by to current user"""
        serializer.save(created_by=self.request.user)


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
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filterset_fields = ['is_active']
    search_fields = ['first_name', 'last_name', 'email', 'document_id']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['first_name', 'last_name']
    
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
        """Procesa un archivo Excel para generar certificados masivamente"""
        
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
            
            # Procesar Excel
            result = BulkCertificateGeneratorService.generate_from_excel(
                excel_file=file_bytes,
                user=request.user
            )
            
            # Convertir resultado a diccionario
            result_dict = result.to_dict()
            
            # Log de resumen
            print(result.get_summary())
            
            return Response(
                result_dict,
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {
                    'error': 'Error al procesar archivo Excel',
                    'detail': str(e)
                },
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
            
            logger.info(f"Preview: {len(data)} registros extraídos por usuario {request.user}")
            
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
            logger.error(f"Error en preview: {str(e)}")
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
            logger.info(f"Procesamiento: {result.successful}/{result.total_rows} exitosos por usuario {request.user}")
            
            return Response(
                result.to_dict(),
                status=status.HTTP_200_OK
            )
            
        except ExcelImportError as e:
            logger.error(f"Error en procesamiento: {str(e)}")
            return Response(
                {
                    'error': 'Error al procesar registros',
                    'detail': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error inesperado en procesamiento: {str(e)}")
            return Response(
                {
                    'error': 'Error inesperado al procesar registros',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

