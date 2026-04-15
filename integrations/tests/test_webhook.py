"""Webhook auth and parsing tests."""
import json
from django.test import TestCase, Client, override_settings
from django.core.cache import cache

from integrations.models import IntegrationSettings, RawDeviceEvent


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "webhook_test"}
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class WebhookSecretTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.integration = IntegrationSettings.get_settings()
        self.integration.webhook_enabled = True
        self.integration.webhook_secret = "test-secret-xyz"
        self.integration.save()

    def test_rejects_without_secret(self):
        payload = json.dumps(
            {"employee_id": "X", "event_type": "check_in", "timestamp": "2025-01-01T09:00:00Z", "event_id": "e1"}
        )
        r = self.client.post(
            "/integrations/webhook/",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)
        data = r.json()
        self.assertEqual(data.get("reason"), "unauthorized")

    def test_accepts_x_webhook_secret_header(self):
        payload = json.dumps(
            {"employee_id": "X", "event_type": "check_in", "timestamp": "2025-01-01T09:00:00Z", "event_id": "e2"}
        )
        r = self.client.post(
            "/integrations/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="test-secret-xyz",
        )
        self.assertEqual(r.status_code, 202)
        self.assertTrue(r.json().get("ok"))
        self.assertEqual(RawDeviceEvent.objects.count(), 1)
        self.assertEqual(RawDeviceEvent.objects.first().status, RawDeviceEvent.STATUS_UNMATCHED)

    def test_accepts_query_secret(self):
        payload = json.dumps(
            {"employee_id": "X", "event_type": "check_in", "timestamp": "2025-01-01T09:00:00Z", "event_id": "e3"}
        )
        r = self.client.post(
            "/integrations/webhook/?secret=test-secret-xyz",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 202)
        self.assertEqual(RawDeviceEvent.objects.count(), 1)
