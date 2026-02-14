"""Telegram settings (singleton)."""
from django.db import models


class TelegramSettings(models.Model):
    """Bot token and chat ID for notifications."""
    bot_token = models.CharField(max_length=255, blank=True)
    chat_id = models.CharField(max_length=100, blank=True)
    enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Telegram Settings"
        verbose_name_plural = "Telegram Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
