from django.db import models
from users.models import User


class Instructor(models.Model):
    id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    specialty = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    signature_url = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_instructors')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructors'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.specialty})" if self.specialty else self.full_name