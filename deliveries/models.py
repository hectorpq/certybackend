from django.db import models

from certificados.models import Certificate
from users.models import User


class DeliveryLog(models.Model):
    METHOD_CHOICES = (
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
        ("link", "Link"),
    )

    STATUS_CHOICES = (
        ("success", "Success"),
        ("error", "Error"),
        ("pending", "Pending"),
    )

    id = models.BigAutoField(primary_key=True)
    certificate = models.ForeignKey(
        Certificate, on_delete=models.CASCADE, related_name="deliveries"
    )
    sent_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="delivery_logs"
    )
    delivery_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    recipient = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["delivery_method"]),
            models.Index(fields=["certificate"]),
        ]
        verbose_name = "Delivery Log"
        verbose_name_plural = "Delivery Logs"

    def __str__(self):
        return f"{self.certificate.participant.first_name} - {self.delivery_method} [{self.status}]"

    @property
    def is_successful(self):
        """Check if delivery was successful"""
        return self.status == "success"

    @property
    def is_failed(self):
        """Check if delivery failed"""
        return self.status == "error"

    @property
    def is_pending(self):
        """Check if delivery is pending"""
        return self.status == "pending"

    def get_delivery_icon(self):
        """Get emoji icon for method"""
        icons = {
            "email": "✉️",
            "whatsapp": "💬",
            "link": "🔗",
        }
        return icons.get(self.delivery_method, "📤")

    def get_status_icon(self):
        """Get emoji icon for status"""
        icons = {
            "success": "✅",
            "error": "❌",
            "pending": "⏳",
        }
        return icons.get(self.status, "❓")
