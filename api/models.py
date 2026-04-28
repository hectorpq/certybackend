from django.db import models
from users.models import User
from certificados.models import Certificate


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('certificate_generated', 'Certificate Generated'),
        ('certificate_delivered', 'Certificate Delivered'),
        ('certificate_retried',   'Certificate Retried'),
        ('user_login',            'User Login'),
        ('user_login_failed',     'User Login Failed'),
        ('export_requested',      'Export Requested'),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs',
    )
    certificate = models.ForeignKey(
        Certificate, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        who = self.user.email if self.user else 'anonymous'
        return f'[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} by {who}'
