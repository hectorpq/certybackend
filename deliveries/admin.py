from django.contrib import admin, messages
from django.utils.html import format_html

from core.admin_utils import color_badge

from .models import DeliveryLog


@admin.register(DeliveryLog)
class DeliveryLogAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "certificate_event",
        "icons_display",
        "status_badge",
        "sent_at",
        "sent_by",
    )
    list_filter = ("status", "delivery_method", "sent_at")
    search_fields = (
        "certificate__student__first_name",
        "certificate__student__last_name",
        "recipient",
        "certificate__event__name",
    )
    readonly_fields = (
        "id",
        "sent_at",
        "updated_at",
        "certificate_info",
        "delivery_info",
    )
    actions = ["retry_delivery", "mark_as_successful"]

    fieldsets = (
        (
            "Delivery Information",
            {"fields": ("id", "certificate_info", "delivery_info")},
        ),
        ("Recipient", {"fields": ("recipient",)}),
        ("Status & Error", {"fields": ("status", "error_message")}),
        (
            "Management",
            {"fields": ("sent_by", "sent_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    ordering = ["-sent_at"]
    date_hierarchy = "sent_at"

    def student_name(self, obj):
        return f"{obj.certificate.participant.first_name} {obj.certificate.participant.last_name}"

    student_name.short_description = "Student"

    def certificate_event(self, obj):
        return obj.certificate.event.name

    certificate_event.short_description = "Event"

    def icons_display(self, obj):
        """Show method and status icons together"""
        method_icon = obj.get_delivery_icon()
        status_icon = obj.get_status_icon()
        return format_html("{} {}", method_icon, status_icon)

    icons_display.short_description = "📤"

    def method_badge(self, obj):
        colors = {"email": "blue", "whatsapp": "green", "link": "purple"}
        return color_badge(colors.get(obj.delivery_method, "gray"), obj.get_delivery_method_display())

    method_badge.short_description = "Method"

    def status_badge(self, obj):
        colors = {"success": "green", "error": "red", "pending": "orange"}
        return color_badge(colors.get(obj.status, "gray"), obj.get_status_display())

    status_badge.short_description = "Status"

    def certificate_info(self, obj):
        code = obj.certificate.verification_code or "Not generated"
        code_display = f"{code[:20]}..." if len(code) > 20 else code
        return format_html(
            '<b>{}</b><br/>Code: <code style="background: #f0f0f0; padding: 2px 5px;">{}</code><br/>Event: {}',
            obj.certificate.participant.full_name,
            code_display,
            obj.certificate.event.name,
        )

    certificate_info.short_description = "Certificate"

    def delivery_info(self, obj):
        icon = obj.get_delivery_icon()
        return format_html(
            "<b>Method:</b> {} {}<br/><b>Recipient:</b> {}<br/><b>Status:</b> {}",
            icon,
            obj.get_delivery_method_display(),
            obj.recipient,
            obj.get_status_display(),
        )

    delivery_info.short_description = "Delivery Details"

    # ========== CUSTOM ACTIONS ==========

    def retry_delivery(self, request, queryset):
        """Action: Retry failed deliveries"""
        failed_count = queryset.filter(status="error").count()
        queryset.filter(status="error").update(status="pending")

        if failed_count > 0:
            self.message_user(
                request,
                f"↩️  {failed_count} failed deliveries marked for retry",
                messages.INFO,
            )
        else:
            self.message_user(request, "No failed deliveries to retry", messages.WARNING)

    retry_delivery.short_description = "↩️  Retry Failed Deliveries"

    def mark_as_successful(self, request, queryset):
        """Action: Manually mark deliveries as successful"""
        count = queryset.exclude(status="success").update(status="success")

        if count > 0:
            self.message_user(request, f"✅ {count} deliveries marked as successful", messages.SUCCESS)

    mark_as_successful.short_description = "✅ Mark as Successful"
