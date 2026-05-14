from django.contrib import admin
from django.utils.html import format_html

from core.admin_utils import BOLD_FORMAT, color_badge

from .models import Enrollment, Event, EventCategory, EventInstructor


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "event_count")
    search_fields = ("name",)
    ordering = ["name"]

    def event_count(self, obj):
        count = obj.events.count()
        return format_html(BOLD_FORMAT, count)

    event_count.short_description = "Events"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "event_date",
        "category",
        "status_badge",
        "instructor_count",
        "enrollment_count",
        "created_by",
    )
    list_filter = ("status", "event_date", "category", "created_at")
    search_fields = ("name", "description", "location")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "instructors_info",
        "enrollments_info",
    )

    fieldsets = (
        ("Event Information", {"fields": ("id", "name", "description", "category")}),
        ("Schedule", {"fields": ("event_date", "end_date", "duration_hours")}),
        ("Location", {"fields": ("location",)}),
        ("Status & Creator", {"fields": ("status", "created_by")}),
        ("Instructors", {"fields": ("instructors_info",), "classes": ("collapse",)}),
        ("Enrollments", {"fields": ("enrollments_info",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    ordering = ["-event_date"]
    date_hierarchy = "event_date"

    def status_badge(self, obj):
        colors = {
            "draft": "gray",
            "active": "green",
            "finished": "blue",
            "cancelled": "red",
        }
        return color_badge(colors.get(obj.status, "gray"), obj.get_status_display())

    status_badge.short_description = "Status"

    def instructor_count(self, obj):
        count = obj.instructors.count()
        return format_html(BOLD_FORMAT, count)

    instructor_count.short_description = "Instructors"

    def enrollment_count(self, obj):
        count = obj.enrollments.count()
        return format_html(BOLD_FORMAT, count)

    enrollment_count.short_description = "Enrollments"

    def instructors_info(self, obj):
        instructors = obj.instructors.all()
        if not instructors:
            return "No instructors assigned"
        return "\n".join([f"• {e.instructor.full_name} - {e.role}" for e in instructors])

    instructors_info.short_description = "Assigned Instructors"

    def enrollments_info(self, obj):
        enrollments = obj.enrollments.all()
        if not enrollments:
            return "No enrollments"
        attending = enrollments.filter(attendance=True).count()
        total = enrollments.count()
        return f"Total: {total} | Attending: {attending}"

    enrollments_info.short_description = "Enrollment Statistics"


class EventInstructorInline(admin.TabularInline):
    model = EventInstructor
    extra = 0
    fields = ("instructor", "role")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "event_name",
        "enrolled_at",
        "attendance_badge",
        "grade",
    )
    list_filter = ("attendance", "enrolled_at", "event")
    search_fields = ("student__first_name", "student__last_name", "event__name")
    readonly_fields = ("id", "enrolled_at")

    fieldsets = (
        ("Enrollment", {"fields": ("student", "event", "enrolled_at")}),
        ("Performance", {"fields": ("attendance", "grade", "notes")}),
    )

    ordering = ["-enrolled_at"]
    date_hierarchy = "enrolled_at"

    def student_name(self, obj):
        return f"{obj.participant.first_name} {obj.participant.last_name}"

    student_name.short_description = "Student"

    def event_name(self, obj):
        return obj.event.name

    event_name.short_description = "Event"

    def attendance_badge(self, obj):
        if obj.attendance:
            return format_html('<span style="color: green; font-weight: bold;">✓ Present</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Absent</span>')

    attendance_badge.short_description = "Attendance"


@admin.register(EventInstructor)
class EventInstructorAdmin(admin.ModelAdmin):
    list_display = ("event", "instructor_name", "instructor_specialty", "role")
    list_filter = ("role", "event")
    search_fields = ("event__name", "instructor__full_name", "instructor__specialty")
    readonly_fields = ("id",)

    def instructor_name(self, obj):
        return obj.instructor.full_name

    instructor_name.short_description = "Instructor"

    def instructor_specialty(self, obj):
        return obj.instructor.specialty or "No specialty"

    instructor_specialty.short_description = "Specialty"
