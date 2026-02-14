from django.contrib import admin
from .models import IntegrationSettings


@admin.register(IntegrationSettings)
class IntegrationSettingsAdmin(admin.ModelAdmin):
    list_display = ["device_ip", "webhook_enabled", "updated_at"]
