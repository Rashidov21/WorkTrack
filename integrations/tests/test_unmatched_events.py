"""Tests for unmatched raw event admin workflow."""
from datetime import time

from django.test import TestCase, Client, override_settings

from accounts.models import User
from employees.models import Employee
from integrations.models import RawDeviceEvent


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class UnmatchedEventsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin1",
            password="testpass123",
            role="admin",
        )
        self.client.force_login(self.admin)

    def test_unmatched_page_lists_events(self):
        RawDeviceEvent.objects.create(
            status=RawDeviceEvent.STATUS_UNMATCHED,
            payload_json={"employee_id": "X", "event_type": "check_in", "timestamp": "2026-04-15T09:00:00Z"},
        )
        r = self.client.get("/integrations/events/unmatched/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "unmatched")

    def test_resolve_raw_event_updates_payload_and_replays(self):
        emp = Employee.objects.create(
            employee_id="EMP100",
            first_name="Ali",
            last_name="Valiyev",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
        )
        raw = RawDeviceEvent.objects.create(
            status=RawDeviceEvent.STATUS_UNMATCHED,
            payload_json={
                "employee_id": "UNKNOWN",
                "event_type": "check_in",
                "timestamp": "2026-04-15T09:30:00Z",
                "event_id": "evt-100",
            },
        )
        r = self.client.post(f"/integrations/events/{raw.pk}/resolve/", data={"employee_id": emp.employee_id})
        self.assertEqual(r.status_code, 302)
        raw.refresh_from_db()
        self.assertEqual(raw.payload_json.get("employee_id"), "EMP100")
        self.assertEqual(raw.status, RawDeviceEvent.STATUS_PROCESSED)

    def test_replay_raw_event_endpoint(self):
        raw = RawDeviceEvent.objects.create(
            status=RawDeviceEvent.STATUS_FAILED,
            payload_json={
                "employee_id": "UNKNOWN",
                "event_type": "check_in",
                "timestamp": "2026-04-15T09:30:00Z",
                "event_id": "evt-200",
            },
        )
        r = self.client.post(f"/integrations/events/{raw.pk}/replay/")
        self.assertEqual(r.status_code, 302)
        raw.refresh_from_db()
        # Replayed event has no matching employee, should end up unmatched.
        self.assertEqual(raw.status, RawDeviceEvent.STATUS_UNMATCHED)
