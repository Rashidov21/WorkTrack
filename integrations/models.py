"""Integration settings and device ingestion models."""
import uuid
from django.db import models


class IntegrationSettings(models.Model):
    """Hikvision device and webhook settings."""
    device_ip = models.CharField(max_length=50, blank=True)
    api_username = models.CharField(max_length=100, blank=True)
    api_password = models.CharField(max_length=255, blank=True)
    webhook_enabled = models.BooleanField(default=True)
    # Secret token for webhook auth: device sends X-Webhook-Secret header
    webhook_secret = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Integration Settings"
        verbose_name_plural = "Integration Settings"

    def save(self, *args, **kwargs):
        # Singleton: only one row
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RawDeviceEvent(models.Model):
    """Durable raw ingress event from webhook/device."""

    STATUS_RECEIVED = "received"
    STATUS_PROCESSED = "processed"
    STATUS_UNMATCHED = "unmatched"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_RECEIVED, "Received"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_UNMATCHED, "Unmatched"),
        (STATUS_FAILED, "Failed"),
    ]

    trace_id = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    device_ip = models.CharField(max_length=64, blank=True)
    external_event_id = models.CharField(max_length=255, blank=True, db_index=True)
    payload_json = models.JSONField(default=dict)
    event_time_device = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RECEIVED, db_index=True)
    retry_count = models.PositiveIntegerField(default=0)
    error_code = models.CharField(max_length=64, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Raw Device Event"
        verbose_name_plural = "Raw Device Events"

    def __str__(self):
        return f"{self.trace_id} {self.status}"


class DeviceImportJob(models.Model):
    """Track historical import job from device API."""

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    date_from = models.DateField()
    date_to = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    fetched_count = models.PositiveIntegerField(default=0)
    queued_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    last_cursor = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Device Import Job"
        verbose_name_plural = "Device Import Jobs"

    def __str__(self):
        return f"{self.date_from}..{self.date_to} ({self.status})"
