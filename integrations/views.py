"""Webhook endpoint and settings UI."""
import json
import logging
import time
from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.conf import settings as django_settings
from django.core.cache import cache
from core.decorators import admin_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import IntegrationSettings
from .tasks import process_device_event

logger = logging.getLogger(__name__)


def _hikvision_event_to_payload(data):
    """
    Hikvision AccessControllerEvent JSON ni WorkTrack payload ga aylantiradi.
    data: loyiha qabul qiladigan dict (employee_id, event_type, timestamp, event_id).
    """
    inner = data.get("AccessControllerEvent") or {}
    timestamp = data.get("dateTime") or ""
    employee_id = (
        inner.get("employeeNoString")
        or data.get("employeeNoString")
        or data.get("personId")
        or data.get("cardNo")
        or data.get("employee_id")
        or inner.get("personId")
        or inner.get("cardNo")
        or inner.get("employee_id")
        or inner.get("serialNo")
        or inner.get("SerialNo")
        or data.get("serialNo")
        or data.get("SerialNo")
        or inner.get("frontSerialNo")
        or data.get("frontSerialNo")
    )
    if employee_id is None:
        serial_no = (
            inner.get("serialNo")
            or inner.get("SerialNo")
            or data.get("serialNo")
            or data.get("SerialNo")
        )
        if serial_no is not None:
            employee_id = str(serial_no)
    if employee_id is not None:
        employee_id = str(employee_id)
    sub_event = inner.get("subEventType") or data.get("subEventType")
    event_type = "check_in"
    if sub_event is not None:
        if sub_event in (1025, 2049):
            event_type = "check_out"
        elif sub_event in (1024, 2048):
            event_type = "check_in"
    event_id = (
        data.get("event_id")
        or f"{data.get('shortSerialNumber', '')}_{timestamp}_{inner.get('serialNo', '')}"
    )
    return {
        "employee_id": employee_id or "",
        "event_type": event_type,
        "timestamp": timestamp,
        "event_id": str(event_id).strip() or "",
    }


def _get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return (xff.split(",")[0].strip() if xff else None) or request.META.get("REMOTE_ADDR") or "unknown"


@method_decorator(csrf_exempt, name="dispatch")
class DeviceWebhookView(View):
    """
    Receive HTTP POST from Hikvision device (or simulator).
    CSRF exempt; rate limit per IP. Secret tekshirilmaydi (qurilma yuborolmaydi).
    """
    def post(self, request):
        content_type = request.META.get("CONTENT_TYPE", "").lower()

        if "multipart/form-data" in content_type:
            raw = request.POST.get("AccessControllerEvent")
            if not raw:
                logger.warning("webhook multipart: AccessControllerEvent part missing")
                return HttpResponseBadRequest("Missing AccessControllerEvent")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.warning("webhook multipart: invalid JSON in AccessControllerEvent: %s", e)
                return HttpResponseBadRequest("Invalid JSON in AccessControllerEvent")
            logger.warning(
                "webhook multipart keys: data=%s inner=%s",
                list(data.keys()),
                list((data.get("AccessControllerEvent") or {}).keys()),
            )
            event_type_raw = data.get("eventType") or ""
            inner_raw = data.get("AccessControllerEvent")
            if (
                event_type_raw == "heartBeat"
                or not inner_raw
                or (isinstance(inner_raw, (list, dict)) and len(inner_raw) == 0)
            ):
                items = []
            else:
                payload = _hikvision_event_to_payload(data)
                if not payload.get("employee_id"):
                    logger.warning("webhook multipart: no employee_id/personId/serialNo in payload")
                items = [payload]
        else:
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return HttpResponseBadRequest("Invalid JSON")
            if not isinstance(body, dict):
                items = body if isinstance(body, list) else [body]
            else:
                items = [body]

        integration = IntegrationSettings.get_settings()
        if not integration.webhook_enabled:
            return JsonResponse({"ok": False, "reason": "webhook_disabled"}, status=503)

        ip = _get_client_ip(request)
        minute_bucket = int(time.time() // 60)
        cache_key = f"webhook_rate_{ip}_{minute_bucket}"
        limit = getattr(django_settings, "WEBHOOK_RATE_LIMIT", 120)
        current = cache.get(cache_key, 0)
        if current >= limit:
            return JsonResponse({"ok": False, "reason": "rate_limit_exceeded"}, status=429)
        cache.set(cache_key, current + 1, timeout=120)

        results = []
        for item in items:
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
