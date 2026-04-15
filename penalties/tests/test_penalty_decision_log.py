"""Penalty decision log tests for auto penalty flow."""
from datetime import date, time
from decimal import Decimal

from django.test import TestCase

from attendance.models import LatenessRecord
from employees.models import Employee
from penalties.models import PenaltyRule, PenaltyDecisionLog
from penalties.services import apply_penalty_for_lateness


class PenaltyDecisionLogTests(TestCase):
    def setUp(self):
        self.emp = Employee.objects.create(
            employee_id="EMP900",
            first_name="Vali",
            last_name="Aliyev",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
        )

    def test_logs_skip_when_no_rule(self):
        late = LatenessRecord.objects.create(
            employee=self.emp,
            date=date(2026, 4, 15),
            minutes_late=20,
            check_in_time="2026-04-15T09:20:00+05:00",
            expected_start=time(9, 0),
        )
        p = apply_penalty_for_lateness(late)
        self.assertIsNone(p)
        log = PenaltyDecisionLog.objects.get(lateness_record=late)
        self.assertEqual(log.decision, PenaltyDecisionLog.DECISION_SKIPPED)
        self.assertEqual(log.reason_code, "no_active_rule")

    def test_logs_created_penalty(self):
        PenaltyRule.objects.create(
            name="Global per minute",
            rule_type="per_minute",
            amount_per_unit=Decimal("1000"),
            is_active=True,
            department="",
        )
        late = LatenessRecord.objects.create(
            employee=self.emp,
            date=date(2026, 4, 16),
            minutes_late=10,
            check_in_time="2026-04-16T09:10:00+05:00",
            expected_start=time(9, 0),
        )
        p = apply_penalty_for_lateness(late)
        self.assertIsNotNone(p)
        log = PenaltyDecisionLog.objects.filter(lateness_record=late).order_by("-created_at").first()
        self.assertEqual(log.decision, PenaltyDecisionLog.DECISION_CREATED)
        self.assertEqual(log.reason_code, "amount_penalty")
        self.assertEqual(log.penalty_id, p.id)
