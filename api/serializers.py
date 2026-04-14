"""
Serializers for Certificate and Delivery APIs
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from certificados.models import Certificate
from deliveries.models import DeliveryLog
from students.models import Student
from events.models import Event
from users.models import User


class StudentSimpleSerializer(serializers.ModelSerializer):
    """Simple student serializer (used in nested contexts)"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'full_name', 'email', 'phone']
        read_only_fields = ['id', 'full_name', 'email', 'phone']


class EventSimpleSerializer(serializers.ModelSerializer):
    """Simple event serializer (used in nested contexts)"""
    class Meta:
        model = Event
        fields = ['id', 'name', 'event_date', 'category']
        read_only_fields = fields


class DeliveryLogSerializer(serializers.ModelSerializer):
    """Serializer for delivery logs"""
    delivery_method_display = serializers.CharField(
        source='get_delivery_method_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_successful = serializers.SerializerMethodField()
    is_failed = serializers.SerializerMethodField()
    is_pending = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryLog
        fields = [
            'id', 'certificate', 'delivery_method', 'delivery_method_display',
            'recipient', 'status', 'status_display', 'error_message',
            'sent_at', 'updated_at', 'sent_by', 'is_successful', 'is_failed', 'is_pending'
        ]
        read_only_fields = ['id', 'sent_at', 'updated_at', 'is_successful', 'is_failed', 'is_pending']
    
    def get_is_successful(self, obj):
        return obj.is_successful
    
    def get_is_failed(self, obj):
        return obj.is_failed
    
    def get_is_pending(self, obj):
        return obj.is_pending


class CertificateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for certificate lists"""
    student = StudentSimpleSerializer(read_only=True)
    event = EventSimpleSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'student', 'event', 'status', 'status_display',
            'verification_code', 'issued_at', 'expires_at', 'is_expired'
        ]
        read_only_fields = fields
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class CertificateDetailSerializer(serializers.ModelSerializer):
    """Full serializer for certificate details"""
    student = StudentSimpleSerializer(read_only=True)
    event = EventSimpleSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    delivery_history = DeliveryLogSerializer(
        source='get_delivery_history',
        many=True,
        read_only=True
    )
    last_delivery = serializers.SerializerMethodField()
    has_delivery_attempts = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'student', 'event', 'template', 'status', 'status_display',
            'verification_code', 'pdf_url', 'issued_at', 'updated_at', 'expires_at',
            'generated_by', 'delivery_history', 'last_delivery', 'has_delivery_attempts',
            'is_expired'
        ]
        read_only_fields = fields
    
    def get_last_delivery(self, obj):
        last = obj.last_delivery_attempt
        if last:
            return DeliveryLogSerializer(last).data
        return None
    
    def get_has_delivery_attempts(self, obj):
        return obj.has_delivery_attempts()
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class CertificateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating certificates"""
    student_id = serializers.IntegerField(write_only=True)
    event_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Certificate
        fields = ['student_id', 'event_id', 'template']
    
    def create(self, validated_data):
        from students.models import Student
        from events.models import Event
        
        student = Student.objects.get(id=validated_data['student_id'])
        event = Event.objects.get(id=validated_data['event_id'])
        
        certificate, created = Certificate.objects.get_or_create(
            student=student,
            event=event,
            defaults={'status': 'pending'}
        )
        
        if not created:
            raise serializers.ValidationError(
                "Certificate already exists for this student and event"
            )
        
        return certificate


class CertificateGenerateSerializer(serializers.Serializer):
    """Serializer for generating certificates"""
    template_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate(self, data):
        # Validate in view context where we have the certificate instance
        return data


class CertificateDeliverSerializer(serializers.Serializer):
    """Serializer for delivering certificates"""
    method = serializers.ChoiceField(choices=['email', 'whatsapp', 'link'])
    recipient = serializers.CharField(required=False, allow_blank=True)
    
    def validate_method(self, value):
        if value not in ['email', 'whatsapp', 'link']:
            raise serializers.ValidationError(
                "Invalid delivery method. Choose from: email, whatsapp, link"
            )
        return value


class EventSerializer(serializers.ModelSerializer):
    """Full serializer for events"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'category', 'category_name', 'created_by', 'created_by_name',
            'name', 'description', 'event_date', 'end_date', 'duration_hours',
            'location', 'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at', 'status_display']


class StudentSerializer(serializers.ModelSerializer):
    """Full serializer for students"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'document_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class UserRegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password_confirm']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=password
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login (get user info)"""
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    role = serializers.CharField()


class UserAuthSerializer(serializers.Serializer):
    """Serializer for user authentication with credentials"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        # Autenticar usando email como username
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError("Email o contraseña incorrectos.")
        
        if not user.is_active:
            raise serializers.ValidationError("Esta cuenta está inactiva.")
        
        data['user'] = user
        return data


class ExcelBulkImportSerializer(serializers.Serializer):
    """
    Serializer para importación masiva de certificados desde Excel
    
    Campos:
    - excel_file: Archivo .xlsx con datos de estudiantes y eventos
    - dry_run: (Opcional) Validar sin guardar cambios
    """
    excel_file = serializers.FileField(
        required=True,
        help_text="Archivo Excel con columnas: full_name, email, document_id, event_name"
    )
    dry_run = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Si es True, valida sin guardar"
    )
    
    def validate_excel_file(self, file):
        """Valida que sea un archivo Excel válido"""
        if not file.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                "Solo se permiten archivos Excel (.xlsx o .xls)"
            )
        
        # Validar tamaño máximo (50 MB)
        if file.size > 52428800:
            raise serializers.ValidationError(
                "El archivo no puede superar 50 MB"
            )
        
        return file


class BulkImportResultSerializer(serializers.Serializer):
    """
    Serializer para el resultado de una importación masiva
    
    Retorna:
    - total_rows: Total de filas procesadas
    - successful: Cantidad exitosa
    - failed: Cantidad de fallos
    - success_rate: Porcentaje de éxito
    - errors: Listado de errores por fila
    - created_certificates: IDs de certificados creados
    """
    processing_timestamp = serializers.DateTimeField()
    total_rows = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    success_rate = serializers.CharField()
    errors = serializers.ListField(child=serializers.DictField())
    created_certificates = serializers.ListField(child=serializers.IntegerField())
    data_preview = serializers.ListField(child=serializers.DictField())
    summary = serializers.CharField()


class ExcelDataPreviewSerializer(serializers.Serializer):
    """
    Serializer para obtener vista previa de datos de un Excel
    sin procesarlos aún
    """
    excel_file = serializers.FileField()
    preview_rows = serializers.IntegerField(default=5, min_value=1, max_value=100)


class CertificateFromExcelSerializer(serializers.Serializer):
    """
    Serializer para datos de un certificado extraído de Excel
    antes de confirmar su generación
    """
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField()
    email = serializers.EmailField()
    document_id = serializers.CharField()
    event_name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(default='pending')
    error = serializers.CharField(required=False, allow_null=True)

