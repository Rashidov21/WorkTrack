from django.contrib import admin
from .models import IntegrationSettings, RawDeviceEvent, DeviceImportJob


@admin.register(IntegrationSettings)
class IntegrationSettingsAdmin(admin.ModelAdmin):
    list_display = ["device_ip", "webhook_enabled", "updated_at"]


@admin.register(RawDeviceEvent)
class RawDeviceEventAdmin(admin.ModelAdmin):
    list_display = ["id", "trace_id", "status", "device_ip", "external_event_id", "received_at", "processed_at"]
    list_filter = ["status", "received_at"]
    search_fields = ["trace_id", "external_event_id", "device_ip"]
    readonly_fields = ["trace_id", "received_at", "processed_at", "payload_json", "error_code", "error_message"]


@admin.register(DeviceImportJob)
class DeviceImportJobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "date_from",
        "date_to",
        "status",
        "fetched_count",
        "queued_count",
        "failed_count",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    readonly_fields = ["started_at", "finished_at", "created_at", "error_message"]
