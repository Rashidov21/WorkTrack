from django.contrib import admin
from .models import TelegramSettings


@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    list_display = ["enabled", "updated_at"]
