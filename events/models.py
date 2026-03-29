from django.db import models
from users.models import User
from students.models import Student
from instructors.models import Instructor

class EventCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Event Categories'

    def __str__(self):
        return self.name

class Event(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    )

    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='events')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    duration_hours = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.event_date.strftime('%d/%m/%Y')})"

class EventInstructor(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="instructors"
    )
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name="events"
    )
    role = models.CharField(max_length=50, default='principal')

    class Meta:
        unique_together = ('event', 'instructor')
        verbose_name = 'Event Instructor'
        verbose_name_plural = 'Event Instructors'

    def __str__(self):
        return f"{self.event.name} - {self.instructor.full_name} ({self.role})"

class Enrollment(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    attendance = models.BooleanField(default=False)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'event')
        ordering = ['enrolled_at']
        indexes = [
            models.Index(fields=['student', 'event']),
            models.Index(fields=['attendance']),
        ]

    def __str__(self):
        attendance_mark = "✓" if self.attendance else "✗"
        return f"{self.student.first_name} - {self.event.name} [{attendance_mark}]"