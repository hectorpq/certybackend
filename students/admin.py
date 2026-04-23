from django.contrib import admin
from django.utils.html import format_html
from .models import Student
from core.admin_utils import active_badge, BOLD_FORMAT


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('document_id', 'full_name', 'email', 'phone', 'status_badge', 'enrollment_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('document_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'enrollment_info')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('id', 'first_name', 'last_name', 'email')
        }),
        ('Document & Contact', {
            'fields': ('document_id', 'phone')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Enrollment Information', {
            'fields': ('enrollment_info',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'

    def status_badge(self, obj):
        return active_badge(obj)
    status_badge.short_description = 'Status'

    def enrollment_count(self, obj):
        count = obj.enrollments.count()
        return format_html(BOLD_FORMAT, count)
    enrollment_count.short_description = 'Enrollments'

    def enrollment_info(self, obj):
        enrollments = obj.enrollments.all()
        if not enrollments:
            return "No enrollments"
        return "\n".join([f"• {e.event.name} ({e.event.event_date.strftime('%d/%m/%Y')})" 
                         for e in enrollments])
    enrollment_info.short_description = 'Student Enrollments'