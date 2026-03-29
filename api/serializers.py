"""
Serializers for Certificate and Delivery APIs
"""
from rest_framework import serializers
from certificados.models import Certificate
from deliveries.models import DeliveryLog
from students.models import Student
from events.models import Event


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
