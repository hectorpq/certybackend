"""
Serializers for API endpoints - Minimal working version
"""
from rest_framework import serializers
from events.models import Event, EventCategory, Enrollment, EventInvitation
from certificados.models import Certificate, Template
from students.models import Student
from users.models import User
from instructors.models import Instructor
from deliveries.models import DeliveryLog


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
    
    class Meta:
        model = Event
        fields = [
            'id', 'category', 'created_by', 'instructor', 'instructor_name', 'name', 'description',
            'event_date', 'end_date', 'duration_hours', 'location',
            'status', 'is_active', 'auto_send_certificates',
            'template', 'template_name',
            'invitation_message', 'is_public', 'max_capacity',
            'name_font_size', 'name_x', 'name_y', 'template_image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
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


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'is_staff', 'is_active']


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        from django.contrib.auth import authenticate
        from django.conf import settings
        
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


class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = '__all__'


class CertificateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'


class CertificateDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'


class CertificateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'


class CertificateGenerateSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    event_id = serializers.IntegerField()


class CertificateDeliverSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['email', 'whatsapp'])


class TemplateSerializer(serializers.ModelSerializer):
    background_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = '__all__'
    
    def get_background_image_url(self, obj):
        if obj.background_image:
            return obj.background_image.url
        return obj.background_url or ''


class TemplateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['name', 'category', 'is_active', 'font_color', 'font_family', 'font_size', 'x_coord', 'y_coord']


class TemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['name', 'category', 'is_active', 'font_color', 'font_family', 'font_size', 'x_coord', 'y_coord']


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'event', 'created_by', 'invitation',
            'status', 'invitation_sent', 'certificate_sent',
            'certificate_sent_at', 'certificate_sent_method',
            'enrolled_at', 'attendance', 'grade', 'notes'
        ]


class EventInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventInvitation
        fields = [
            'id', 'event', 'student', 'email',
            'token', 'status', 'expires_at',
            'sent_at', 'responded_at', 'created_by', 'created_at'
        ]


class InvitationDetailSerializer(serializers.ModelSerializer):
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_date = DateField(source='event.event_date', read_only=True)
    event_location = serializers.CharField(source='event.location', read_only=True)
    event_description = serializers.CharField(source='event.description', read_only=True)
    student_exists = serializers.SerializerMethodField()
    
    class Meta:
        model = EventInvitation
        fields = [
            'id', 'event', 'event_name', 'event_date', 'event_location',
            'event_description', 'email', 'status', 'expires_at',
            'student_exists', 'student'
        ]
    
    def get_student_exists(self, obj):
        # Check if student is linked OR if a student with this email exists
        if obj.student:
            return True
        from students.models import Student
        return Student.objects.filter(email__iexact=obj.email).exists()


class InvitationRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(min_length=8)


class DeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLog
        fields = '__all__'


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


# Legacy aliases
CertificateSerializer = CertificateListSerializer
CertificateGenerateSerializer = CertificateGenerateSerializer
CertificateDeliverSerializer = CertificateDeliverSerializer
EventCertificateSerializer = EventSimpleSerializer
EventParticipantWithCertificateSerializer = EventSimpleSerializer
EnrollmentCreateSerializer = EventSimpleSerializer
BulkImportResultSerializer = EventSimpleSerializer
ExcelBulkImportSerializer = EventSimpleSerializer
UserLoginSerializer = UserLoginSerializer
UserAuthSerializer = UserAuthSerializer