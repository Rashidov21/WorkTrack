"""Attendance service tests."""
from datetime import time

from django.test import TestCase

from employees.models import Employee
from attendance.services import resolve_employee_from_device_string, create_log_idempotent


class ResolveEmployeeTests(TestCase):
    def setUp(self):
        self.emp = Employee.objects.create(
            employee_id="E001",
            first_name="A",
            last_name="B",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            device_person_id="HV99",
        )

    def test_by_employee_id(self):
        self.assertEqual(resolve_employee_from_device_string("E001").pk, self.emp.pk)

    def test_by_device_person_id(self):
        self.assertEqual(resolve_employee_from_device_string("HV99").pk, self.emp.pk)

    def test_unknown_returns_none(self):
        self.assertIsNone(resolve_employee_from_device_string("nope"))

    def test_create_log_resolves_device_person_id(self):
        from django.utils import timezone
        ts = timezone.now()
        log, created = create_log_idempotent(
            "HV99",
            "check_in",
            ts.isoformat(),
            source_id="test_hv99_1",
            source="device",
        )
        self.assertTrue(created)
        self.assertEqual(log.employee_id, self.emp.pk)
