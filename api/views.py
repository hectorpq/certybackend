"""
ViewSets (views) for Certificate and Delivery APIs
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from certificados.models import Certificate
from deliveries.models import DeliveryLog
from .serializers import (
    CertificateListSerializer,
    CertificateDetailSerializer,
    CertificateCreateSerializer,
    CertificateGenerateSerializer,
    CertificateDeliverSerializer,
    DeliveryLogSerializer,
)


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
