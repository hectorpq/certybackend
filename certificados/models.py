import hashlib
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from events.models import Event
from participants.models import Participant
from users.models import User


class Template(models.Model):
    """
    Modelo para plantillas de certificados

    Soporta:
    - Imagen de fondo (PNG/JPG)
    - Posiciones configurables para cada campo mediante layout_config
    """

    id = models.BigAutoField(primary_key=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="templates")

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)

    background_image = models.ImageField(
        upload_to="templates/backgrounds/",
        blank=True,
        null=True,
        help_text="Imagen de fondo del certificado (PNG/JPG)",
    )

    background_url = models.TextField(blank=True, help_text="URL de la imagen de fondo (legacy)")
    preview_url = models.TextField(blank=True)

    layout_config = models.JSONField(
        default=dict,
        help_text="""Configuración de posiciones y estilos. Ejemplo:
        {
            "student_name": {"x": 100, "y": 150, "font_size": 24, "font_family": "Arial", "color": "#000000"},
            "event_name": {"x": 100, "y": 200, "font_size": 20, "font_family": "Arial", "color": "#333333"},
            "event_date": {"x": 100, "y": 250, "font_size": 16, "font_family": "Arial", "color": "#666666"},
            "verification_code": {"x": 100, "y": 300, "font_size": 14, "font_family": "Arial", "color": "#999999"}
        }""",
    )

    is_active = models.BooleanField(default=True)

    font_color = models.CharField(max_length=20, default="#000000")
    font_family = models.CharField(max_length=50, default="Helvetica")
    font_size = models.IntegerField(default=24)
    x_coord = models.FloatField(default=100.0)
    y_coord = models.FloatField(default=150.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})" if self.category else self.name


class Certificate(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("generated", "Generated"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    id = models.BigAutoField(primary_key=True)

    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="certificates")

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="certificates")

    template = models.ForeignKey(
        Template,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
    )

    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_certificates",
    )

    verification_code = models.CharField(max_length=50, unique=True)

    pdf_url = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    expires_at = models.DateTimeField(null=True, blank=True)

    issued_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("participant", "event")
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["verification_code"]),
            models.Index(fields=["participant", "event"]),
        ]

    def __str__(self):
        return f"{self.participant} - {self.event.name} [{self.status}]"

    def is_expired(self):
        """Check if certificate has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @staticmethod
    def generate_verification_code(participant_id, event_id):
        """Generate unique verification code from participant and event"""
        code_source = f"{participant_id}{event_id}{timezone.now().isoformat()}".encode()
        return hashlib.md5(code_source, usedforsecurity=False).hexdigest()[:20].upper()  # noqa: S324

    def save(self, *args, **kwargs):
        """Auto-generate verification code if not set"""
        if not self.verification_code:
            self.verification_code = self.generate_verification_code(str(self.participant.id), str(self.event.id))
        super().save(*args, **kwargs)

    def generate(self, template=None, generated_by=None, skip_attendance_check=False):
        """Generate certificate from enrollment"""
        if self.status != "pending":
            raise ValidationError(f"Certificate already {self.status}")

        if not skip_attendance_check:
            from events.models import Enrollment

            try:
                enrollment = Enrollment.objects.get(participant=self.participant, event=self.event)
                if not enrollment.attendance:
                    raise ValidationError("Participant did not attend the event")
            except Enrollment.DoesNotExist:
                raise ValidationError("Participant not enrolled in this event")

        # Generate code if not set
        if not self.verification_code:
            self.verification_code = self.generate_verification_code(str(self.participant.id), str(self.event.id))

        # Set template if provided
        if template:
            self.template = template

        # Set generated by
        if generated_by:
            self.generated_by = generated_by

        # Set expiration (1 year from now)
        self.expires_at = timezone.now() + timedelta(days=365)

        # Generate real PDF
        from services.pdf_service import PDFService

        pdf_result = PDFService.generate_certificate_pdf(self, template or self.template)
        if pdf_result["success"]:
            self.pdf_url = pdf_result["path"]
        else:
            raise ValidationError(f"PDF generation failed: {pdf_result['message']}")

        # Change status
        self.status = "generated"
        self.save()

        return self

    def _determine_recipient(self, method):
        """Determine the recipient email/phone based on delivery method.
        WhatsApp requires a phone number — returns None if absent (caller raises).
        """
        if method == "email":
            return self.participant.email
        elif method == "whatsapp":
            return self.participant.phone or None
        else:  # link
            return self.participant.email

    def _send_delivery(self, method, recipient):
        """Send delivery and return result dict"""
        if method == "email":
            from services.email_service import EmailService

            return EmailService.send_certificate(self, recipient)
        elif method == "whatsapp":
            from services.whatsapp_service import get_whatsapp_service

            try:
                whatsapp = get_whatsapp_service()
                return whatsapp.send_certificate(self, recipient)
            except ModuleNotFoundError:
                return {"success": False, "message": "WhatsApp service not configured"}
        elif method == "link":
            return {"success": True, "message": f"Certificate link: {self.pdf_url}"}
        else:
            raise ValidationError(f"Unknown delivery method: {method}")

    def _update_delivery_status(self, delivery_log, delivery_result):
        """Update delivery log and certificate status based on result"""
        if delivery_result["success"]:
            delivery_log.status = "success"
            self.status = "sent"
        else:
            delivery_log.status = "error"
            delivery_log.error_message = delivery_result["message"]
            self.status = "failed"

    def deliver(self, method="email", recipient=None, sent_by=None):
        """Deliver certificate via email, WhatsApp, or link"""
        if self.status not in ["generated", "sent", "failed"]:
            raise ValidationError("Certificate must be generated first")

        # Determine recipient if not provided
        if not recipient:
            recipient = self._determine_recipient(method)

        if not recipient:
            raise ValidationError(f"No {method} address found for participant")

        # Create delivery log entry
        from deliveries.models import DeliveryLog

        delivery_log = DeliveryLog.objects.create(
            certificate=self,
            delivery_method=method,
            recipient=recipient,
            sent_by=sent_by,
            status="pending",
        )

        # Send delivery and update status
        delivery_result = self._send_delivery(method, recipient)
        self._update_delivery_status(delivery_log, delivery_result)

        # Persist changes
        delivery_log.save()
        self.save()

        return delivery_log

    def mark_as_failed(self, error_message, sent_by=None):
        """Mark certificate as failed and log reason"""
        if self.status == "pending":
            raise ValidationError("Cannot fail a pending certificate")

        self.status = "failed"
        self.save()

        from deliveries.models import DeliveryLog

        DeliveryLog.objects.create(
            certificate=self,
            delivery_method="email",
            sent_by=sent_by,
            status="error",
            error_message=error_message,
        )

        return self

    def get_delivery_history(self):
        """Get all delivery attempts"""
        return self.deliveries.all().order_by("-sent_at")

    def has_delivery_attempts(self):
        """Check if certificate has delivery logs"""
        return self.deliveries.exists()

    @property
    def last_delivery_attempt(self):
        """Get most recent delivery attempt"""
        return self.deliveries.first()

    @property
    def delivery_status(self):
        """Get last delivery status or certificate status"""
        last = self.last_delivery_attempt
        return last.status if last else self.status
