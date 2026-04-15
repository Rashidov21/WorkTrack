"""Tests for device import jobs and backfill flow."""
from datetime import time
from unittest.mock import patch

from django.test import TestCase, Client, override_settings

from accounts.models import User
from employees.models import Employee
from integrations.models import DeviceImportJob, IntegrationSettings, RawDeviceEvent
from integrations.tasks import run_device_import_job


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class DeviceImportJobTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username="admin2", password="testpass123", role="admin")
        self.client.force_login(self.admin)
        self.integration = IntegrationSettings.get_settings()
        self.integration.device_ip = "http://192.168.0.188"
        self.integration.api_username = "admin"
        self.integration.api_password = "secret"
        self.integration.save()

    @patch("integrations.views.run_device_import_job.delay")
    def test_start_import_job_from_settings_page(self, mock_delay):
        r = self.client.post(
            "/integrations/settings/",
            data={
                "start_import": "1",
                "import_date_from": "2026-04-01",
                "import_date_to": "2026-04-15",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(DeviceImportJob.objects.count(), 1)
        mock_delay.assert_called_once()

    @patch("attendance.tasks.run_daily_summary_and_penalties.delay")
    @patch("integrations.tasks.HikvisionClient.fetch_events_page")
    def test_run_import_job_fetches_and_queues_raw_events(self, mock_fetch, mock_daily_delay):
        Employee.objects.create(
            employee_id="EMP001",
            first_name="Ali",
            last_name="Valiyev",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
        )
        mock_fetch.side_effect = [
            {
                "AcsEvent": {
                    "responseStatusStrg": "MORE",
                    "numOfMatches": 1,
                    "totalMatches": 1,
                    "InfoList": [
                        {
                            "employeeNoString": "EMP001",
                            "serialNo": 1234,
                            "time": "2026-04-10T09:20:00+05:00",
                            "label": "Check In",
                        }
                    ],
                }
            },
            {"AcsEvent": {"numOfMatches": 0, "InfoList": []}},
        ]
        job = DeviceImportJob.objects.create(date_from="2026-04-10", date_to="2026-04-10")
        result = run_device_import_job(job.pk)
        self.assertTrue(result.get("ok"))
        job.refresh_from_db()
        self.assertEqual(job.status, DeviceImportJob.STATUS_SUCCESS)
        self.assertEqual(job.fetched_count, 1)
        self.assertEqual(job.queued_count, 1)
        self.assertEqual(RawDeviceEvent.objects.count(), 1)
        mock_daily_delay.assert_called_once_with("2026-04-10")
