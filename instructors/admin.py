from django.contrib import admin
from django.utils.html import format_html

from core.admin_utils import BOLD_FORMAT, active_badge

from .models import Instructor


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "specialty",
        "status_badge",
        "event_count",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("full_name", "email", "specialty")
    readonly_fields = ("id", "created_at", "updated_at", "events_info")

    fieldsets = (
        ("Personal Information", {"fields": ("id", "full_name", "email", "phone")}),
        ("Professional Details", {"fields": ("specialty", "bio", "signature_url")}),
        ("Status", {"fields": ("is_active",)}),
        ("Events", {"fields": ("events_info",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    ordering = ["full_name"]
    date_hierarchy = "created_at"

    def status_badge(self, obj):
        return active_badge(obj)

    status_badge.short_description = "Status"

    def event_count(self, obj):
        count = obj.events.count()
        return format_html(BOLD_FORMAT, count)

    event_count.short_description = "Events"

    def events_info(self, obj):
        events = obj.events.all()
        if not events:
            return "No assigned events"
        return "\n".join([f"• {e.event.name} ({e.event.event_date.strftime('%d/%m/%Y')}) - {e.role}" for e in events])

    events_info.short_description = "Assigned Events"
