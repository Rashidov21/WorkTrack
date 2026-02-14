"""Telegram settings UI and test button."""
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from core.decorators import admin_required
from django.utils.decorators import method_decorator

from .models import TelegramSettings


@method_decorator(admin_required, name="dispatch")
class TelegramSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "notifications/telegram_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["telegram"] = TelegramSettings.get_settings()
        return context

    def post(self, request, *args, **kwargs):
        telegram = TelegramSettings.get_settings()
        if "test" in request.POST:
            # Send test message
            if not telegram.bot_token or not telegram.chat_id:
                messages.error(request, "Avval Bot token va Chat ID ni kiriting.")
                return redirect("notifications:telegram_settings")
            url = f"https://api.telegram.org/bot{telegram.bot_token}/sendMessage"
            try:
                r = requests.post(url, json={"chat_id": telegram.chat_id, "text": "WorkTrack test message."}, timeout=10)
                r.raise_for_status()
                messages.success(request, "Test xabar yuborildi.")
            except Exception as e:
                messages.error(request, f"Xatolik: {e}")
            return redirect("notifications:telegram_settings")

        telegram.bot_token = request.POST.get("bot_token", "").strip()
        telegram.chat_id = request.POST.get("chat_id", "").strip()
        telegram.enabled = request.POST.get("enabled") == "on"
        telegram.save()
        messages.success(request, "Telegram sozlamalari saqlandi.")
        return redirect("notifications:telegram_settings")

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
