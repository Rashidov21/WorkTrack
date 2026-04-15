"""Reconciliation report view tests."""
from datetime import time

from django.test import TestCase, Client

from accounts.models import User
from employees.models import Employee
from integrations.models import RawDeviceEvent


class ReconciliationReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(username="mgr1", password="testpass123", role="manager")
        self.client.force_login(self.manager)
        Employee.objects.create(
            employee_id="EMP777",
            first_name="Test",
            last_name="User",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
        )

    def test_reconciliation_report_page_loads(self):
        RawDeviceEvent.objects.create(
            status=RawDeviceEvent.STATUS_UNMATCHED,
            payload_json={"employee_id": "UNKNOWN", "event_type": "check_in", "timestamp": "2026-04-15T09:00:00+05:00"},
        )
        r = self.client.get("/reports/reconciliation/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Reconciliation")
        self.assertContains(r, "Raw unmatched")
