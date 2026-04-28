from django.contrib import admin
from django.utils.html import format_html
from .models import Participant
from core.admin_utils import active_badge, BOLD_FORMAT


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('document_id', 'full_name', 'email', 'phone', 'status_badge', 'enrollment_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('document_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'enrollment_info')

    fieldsets = (
        ('Información Personal', {
            'fields': ('id', 'first_name', 'last_name', 'email')
        }),
        ('Documento y Contacto', {
            'fields': ('document_id', 'phone')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Información de Matrículas', {
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
    full_name.short_description = 'Nombre Completo'

    def status_badge(self, obj):
        return active_badge(obj)
    status_badge.short_description = 'Estado'

    def enrollment_count(self, obj):
        count = obj.enrollments.count()
        return format_html(BOLD_FORMAT, count)
    enrollment_count.short_description = 'Matrículas'

    def enrollment_info(self, obj):
        enrollments = obj.enrollments.all()
        if not enrollments:
            return "Sin matrículas"
        return "\n".join([f"• {e.event.name} ({e.event.event_date.strftime('%d/%m/%Y')})"
                         for e in enrollments])
    enrollment_info.short_description = 'Matrículas del Participante'
