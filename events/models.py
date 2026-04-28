import uuid

from django.db import models
from django.utils import timezone

from instructors.models import Instructor
from participants.models import Participant
from users.models import User


class EventCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Event Categories"

    def __str__(self):
        return self.name


class Event(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("active", "Active"),
        ("finished", "Finished"),
        ("cancelled", "Cancelled"),
    )

    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events",
    )
    instructor = models.ForeignKey(
        "instructors.Instructor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    duration_hours = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    is_active = models.BooleanField(default=True)
    auto_send_certificates = models.BooleanField(default=False)
    template = models.ForeignKey(
        "certificados.Template", on_delete=models.SET_NULL, null=True, blank=True
    )
    invitation_message = models.TextField(default="", blank=True)
    is_public = models.BooleanField(default=False)
    max_capacity = models.IntegerField(null=True, blank=True)
    name_font_size = models.IntegerField(default=24)
    name_x = models.IntegerField(default=100)
    name_y = models.IntegerField(default=150)
    template_image = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-event_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["event_date"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.event_date.strftime('%d/%m/%Y')})"


class EventInstructor(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_instructors"
    )
    instructor = models.ForeignKey(
        Instructor, on_delete=models.CASCADE, related_name="event_instructor_roles"
    )
    role = models.CharField(max_length=50, default="principal")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="event_instructors"
    )

    class Meta:
        unique_together = ("event", "instructor")
        verbose_name = "Event Instructor"
        verbose_name_plural = "Event Instructors"

    def __str__(self):
        return f"{self.event.name} - {self.instructor.full_name} ({self.role})"


class EventInvitation(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pendiente"),
        ("sent", "Enviada"),
        ("accepted", "Aceptada"),
        ("rejected", "Rechazada"),
        ("expired", "Expirada"),
    )

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="invitations"
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="event_invitations",
        null=True,
        blank=True,
    )
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    expires_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sent_invitations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["status"]),
            models.Index(fields=["email", "event"]),
        ]

    def __str__(self):
        return f"{self.email} - {self.event.name} ({self.get_status_display()})"

    def is_expired(self):
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False


class Enrollment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    )

    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="enrollments"
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="enrollments"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="enrollments"
    )
    invitation = models.ForeignKey(
        EventInvitation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    invitation_sent = models.BooleanField(default=False)
    certificate_sent = models.BooleanField(default=False)
    certificate_sent_at = models.DateTimeField(null=True, blank=True)
    certificate_sent_method = models.CharField(max_length=20, blank=True, default="")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    attendance = models.BooleanField(default=False)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("participant", "event")
        ordering = ["enrolled_at"]
        indexes = [
            models.Index(fields=["participant", "event"]),
            models.Index(fields=["attendance"]),
        ]

    def __str__(self):
        attendance_mark = "✓" if self.attendance else "✗"
        return f"{self.participant.first_name} - {self.event.name} [{attendance_mark}]"
