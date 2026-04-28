from django.db import models

from users.models import User


class Participant(models.Model):
    id = models.BigAutoField(primary_key=True)
    document_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_participants")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["document_id"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.document_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
