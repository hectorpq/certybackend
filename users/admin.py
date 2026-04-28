from django.contrib import admin

from core.admin_utils import color_badge

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "role_badge",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_staff", "created_at")
    search_fields = ("email", "full_name")
    readonly_fields = ("id", "created_at", "updated_at", "password_info")

    fieldsets = (
        ("User Information", {"fields": ("id", "email", "full_name")}),
        (
            "Role & Permissions",
            {"fields": ("role", "is_staff", "is_superuser", "is_active")},
        ),
        (
            "Password",
            {"fields": ("password", "password_info"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def role_badge(self, obj):
        colors = {"admin": "red", "editor": "blue"}
        color = colors.get(obj.role, "gray")
        return color_badge(color, obj.get_role_display())

    role_badge.short_description = "Role"

    def password_info(self, obj):
        return (
            "Use 'Change Password' link below to update password"
            if obj.id
            else "Password will be set after creation"
        )

    password_info.short_description = "Password Change"
