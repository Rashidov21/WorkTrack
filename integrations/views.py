"""Webhook endpoint and settings UI."""
import json
import time
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.conf import settings as django_settings
from django.core.cache import cache
from core.decorators import admin_required
from django.utils.decorators import method_decorator
from .models import IntegrationSettings
from .tasks import process_device_event


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return (xff.split(",")[0].strip() if xff else None) or request.META.get("REMOTE_ADDR") or "unknown"


class DeviceWebhookView(View):
    """
    Receive HTTP POST from Hikvision device (or simulator).
    Protected by optional X-Webhook-Secret header and rate limit per IP.
    """
    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        integration = IntegrationSettings.get_settings()
        if not integration.webhook_enabled:
            return JsonResponse({"ok": False, "reason": "webhook_disabled"}, status=503)

        # Optional: require webhook secret if configured
        if integration.webhook_secret:
            secret = request.headers.get("X-Webhook-Secret") or request.GET.get("secret")
            if secret != integration.webhook_secret:
                return HttpResponseForbidden("Invalid or missing webhook secret")

        # Rate limit by IP
        ip = _get_client_ip(request)
        minute_bucket = int(time.time() // 60)
        cache_key = f"webhook_rate_{ip}_{minute_bucket}"
        limit = getattr(django_settings, "WEBHOOK_RATE_LIMIT", 120)
        current = cache.get(cache_key, 0)
        if current >= limit:
            return JsonResponse({"ok": False, "reason": "rate_limit_exceeded"}, status=429)
        cache.set(cache_key, current + 1, timeout=120)

        if not isinstance(body, dict):
            body = body if isinstance(body, list) else [body]
        else:
            body = [body]

        results = []
        for item in body:
            process_device_event.delay(item)
            results.append({"queued": True})

        return JsonResponse({"ok": True, "processed": len(results), "results": results})


# Settings pages (admin only)
@method_decorator(admin_required, name="dispatch")
class IntegrationSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "integrations/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integration"] = IntegrationSettings.get_settings()
        return context

    def post(self, request, *args, **kwargs):
        if not getattr(request.user, "role", None) == "admin":
            return redirect("core:dashboard")
        integration = IntegrationSettings.get_settings()
        integration.device_ip = request.POST.get("device_ip", "").strip()
        integration.api_username = request.POST.get("api_username", "").strip()
        new_password = request.POST.get("api_password", "")
        if new_password:
            integration.api_password = new_password
        integration.webhook_enabled = request.POST.get("webhook_enabled") == "on"
        ws = (request.POST.get("webhook_secret") or "").strip()
        if ws:
            integration.webhook_secret = ws
        integration.save()
        return redirect("integrations:settings")

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


def _get_or_set_system_setting(key, value=None):
    from core.models import SystemSettings
    obj, _ = SystemSettings.objects.get_or_create(key=key, defaults={"value": value or ""})
    if value is not None:
        obj.value = value
        obj.save()
    return obj.value


@method_decorator(admin_required, name="dispatch")
class PlatformSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "integrations/platform_settings.html"

    def get_context_data(self, **kwargs):
        from core.models import SystemSettings
        context = super().get_context_data(**kwargs)
        defaults = {o.key: o.value for o in SystemSettings.objects.all()}
        context["defaults"] = defaults
        context["default_work_start"] = defaults.get("default_work_start", "09:00")
        context["default_work_end"] = defaults.get("default_work_end", "18:00")
        context["default_grace_period"] = defaults.get("default_grace_period", "5")
        context["default_penalty_per_minute"] = defaults.get("default_penalty_per_minute", "0")
        return context

    def post(self, request, *args, **kwargs):
        if getattr(request.user, "role", None) != "admin":
            return redirect("core:dashboard")
        _get_or_set_system_setting("default_work_start", request.POST.get("default_work_start", "").strip() or "09:00")
        _get_or_set_system_setting("default_work_end", request.POST.get("default_work_end", "").strip() or "18:00")
        _get_or_set_system_setting("default_grace_period", request.POST.get("default_grace_period", "").strip() or "5")
        _get_or_set_system_setting("default_penalty_per_minute", request.POST.get("default_penalty_per_minute", "").strip() or "0")
        return redirect("integrations:platform_settings")

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
