from django.contrib import admin
from .models import SystemSettings, AuditLog


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ["key", "value", "updated_at"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "model_name", "message", "created_at"]
    list_filter = ["action"]
    date_hierarchy = "created_at"
    readonly_fields = ["user", "action", "model_name", "object_id", "message", "ip_address", "created_at"]
