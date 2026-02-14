"""Integration settings: device IP, API credentials, webhook toggle."""
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
