"""
Serializers for API endpoints - Minimal working version
"""
from rest_framework import serializers
from events.models import Event, EventCategory, Enrollment, EventInvitation
from certificados.models import Certificate, Template
from participants.models import Participant
from users.models import User
from instructors.models import Instructor
from deliveries.models import DeliveryLog
from api.models import AuditLog


class DateField(serializers.DateField):
    def to_representation(self, value):
        if value is None:
            return None
        if hasattr(value, 'date'):
            return str(value.date())
        return str(value)

    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        return super().to_internal_value(data)


class EventSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    event_date = DateField()
    end_date = DateField(allow_null=True, required=False)
    template_name = serializers.SerializerMethodField()
    instructor_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'category', 'created_by', 'instructor', 'instructor_name', 'name', 'description',
            'event_date', 'end_date', 'duration_hours', 'location',
            'status', 'status_display', 'is_active', 'auto_send_certificates',
            'template', 'template_name',
            'invitation_message', 'is_public', 'max_capacity',
            'name_font_size', 'name_x', 'name_y', 'template_image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_template_name(self, obj):
        if obj.template:
            return obj.template.name
        return None

    def get_instructor_name(self, obj):
        if obj.instructor:
            return obj.instructor.full_name
        return None


class EventSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'status']


class ParticipantSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Participant
        fields = [
            'id', 'document_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'is_active', 'created_by', 'created_at', 'updated_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'is_staff', 'is_active']


class UserAuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate

        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Credenciales inválidas')
            if not user.is_active:
                raise serializers.ValidationError('Usuario inactivo')
            data['user'] = user
        else:
            raise serializers.ValidationError('Email y contraseña requeridos')

        return data


UserLoginSerializer = UserAuthSerializer


class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class CertificateListSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            'id', 'student', 'event', 'template', 'status', 'status_display',
            'verification_code', 'pdf_url', 'issued_at', 'updated_at', 'expires_at',
            'generated_by',
        ]

    def get_student(self, obj):
        return {
            'id': obj.participant.id,
            'full_name': obj.participant.full_name,
            'email': obj.participant.email,
            'phone': obj.participant.phone or '',
        }

    def get_event(self, obj):
        return {
            'id': obj.event.id,
            'name': obj.event.name,
            'event_date': str(obj.event.event_date) if obj.event.event_date else None,
            'category': obj.event.category,
        }

    def get_status_display(self, obj):
        return obj.get_status_display()


class CertificateDetailSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    delivery_history = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            'id', 'student', 'event', 'template', 'status', 'status_display',
            'verification_code', 'pdf_url', 'issued_at', 'updated_at', 'expires_at',
            'generated_by', 'delivery_history',
        ]

    def get_student(self, obj):
        return {
            'id': obj.participant.id,
            'full_name': obj.participant.full_name,
            'email': obj.participant.email,
            'phone': obj.participant.phone or '',
        }

    def get_event(self, obj):
        return {
            'id': obj.event.id,
            'name': obj.event.name,
            'event_date': str(obj.event.event_date) if obj.event.event_date else None,
            'category': obj.event.category,
        }

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_delivery_history(self, obj):
        logs = obj.deliveries.all().order_by('-sent_at')
        return DeliveryLogSerializer(logs, many=True).data


class CertificateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'


class CertificateGenerateSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField(required=False, allow_null=True)
    event_id = serializers.IntegerField(required=False, allow_null=True)
    template_id = serializers.IntegerField(required=False, allow_null=True)


class CertificateDeliverSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['email', 'whatsapp', 'link'])
    recipient = serializers.CharField(required=False, allow_blank=True)


class TemplateSerializer(serializers.ModelSerializer):
    background_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = '__all__'
    
    def get_background_image_url(self, obj):
        request = self.context.get('request')
        if obj.background_image:
            url = obj.background_image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        if obj.background_url:
            if request and obj.background_url.startswith('/'):
                return request.build_absolute_uri(obj.background_url)
            return obj.background_url
        return ''


class TemplateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'name', 'category', 'is_active', 'font_color', 'font_family', 'font_size', 'x_coord', 'y_coord']
        read_only_fields = ['id']


class TemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'name', 'category', 'is_active', 'font_color', 'font_family', 'font_size', 'x_coord', 'y_coord']
        read_only_fields = ['id']


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            'id', 'participant', 'event', 'created_by', 'invitation',
            'status', 'invitation_sent', 'certificate_sent',
            'certificate_sent_at', 'certificate_sent_method',
            'enrolled_at', 'attendance', 'grade', 'notes'
        ]


class EventInvitationSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()

    class Meta:
        model = EventInvitation
        fields = [
            'id', 'event', 'event_name', 'participant', 'student_name', 'email',
            'token', 'status', 'status_display', 'expires_at',
            'sent_at', 'responded_at', 'created_by', 'created_at'
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_student_name(self, obj):
        return obj.participant.full_name if obj.participant else None

    def get_event_name(self, obj):
        return obj.event.name


class InvitationDetailSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_date = DateField(source='event.event_date', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    event_description = serializers.CharField(source='event.description', read_only=True)
    status_display = serializers.SerializerMethodField()
    student_exists = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()

    class Meta:
        model = EventInvitation
        fields = [
            'id', 'event', 'event_name', 'event_date', 'event_location',
            'event_description', 'email', 'status', 'status_display', 'expires_at',
            'student_exists', 'student', 'participant'
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_student_exists(self, obj):
        if obj.participant:
            return True
        return Participant.objects.filter(email__iexact=obj.email).exists()

    def get_student(self, obj):
        return obj.participant_id


class InvitationRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(min_length=8)


class DeliveryLogSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    delivery_method_display = serializers.SerializerMethodField()
    is_successful = serializers.ReadOnlyField()
    is_failed = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()

    class Meta:
        model = DeliveryLog
        fields = '__all__'

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_delivery_method_display(self, obj):
        return obj.get_delivery_method_display()


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de nuevos usuarios
    """
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    password_confirm = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class ExcelBulkImportSerializer(serializers.Serializer):
    excel_file = serializers.FileField()


class EnrollmentCreateSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField()
    attendance = serializers.BooleanField(required=False, default=False)
    grade = serializers.FloatField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, default='', allow_blank=True)


# Legacy aliases
CertificateSerializer = CertificateListSerializer
EventCertificateSerializer = EventSimpleSerializer
EventParticipantWithCertificateSerializer = EventSimpleSerializer
BulkImportResultSerializer = EventSimpleSerializer
StudentSerializer = ParticipantSerializer  # backward compat alias


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()
    # Override to avoid DRF's GenericIPAddressField Django-5 incompatibility
    ip_address = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'action_display', 'user', 'user_email',
            'certificate', 'ip_address', 'details', 'timestamp',
        ]
        read_only_fields = fields

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_action_display(self, obj):
        return obj.get_action_display()
