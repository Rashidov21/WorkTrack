"""recompute_daily_summary: kelish, kechikish yozuvi, vaqtida / ish kuni emas."""
from datetime import date, datetime, time

from django.test import TestCase, override_settings
from django.utils import timezone

from employees.models import Employee, WorkSchedule
from attendance.models import AttendanceLog, DailySummary, LatenessRecord
from attendance.services import recompute_daily_summary, create_log_idempotent


@override_settings(USE_TZ=True, TIME_ZONE="Asia/Tashkent")
class RecomputeDailySummaryTests(TestCase):
    def setUp(self):
        self.emp = Employee.objects.create(
            employee_id="T001",
            first_name="Test",
            last_name="User",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=5,
        )

    def _aware(self, d: date, t: time):
        dt = datetime.combine(d, t)
        return timezone.make_aware(dt, timezone.get_current_timezone())

    def test_late_check_in_creates_lateness_record(self):
        d = date(2026, 6, 1)  # Monday
        ts = self._aware(d, time(9, 30))
        AttendanceLog.objects.create(
            employee=self.emp,
            event_type="check_in",
            timestamp=ts,
            source_id="late1",
            source="device",
        )
        recompute_daily_summary(self.emp, d)
        self.assertTrue(LatenessRecord.objects.filter(employee=self.emp, date=d).exists())
        s = DailySummary.objects.get(employee=self.emp, date=d)
        self.assertEqual(s.status, DailySummary.STATUS_LATE)
        self.assertGreater(s.minutes_late, 0)

    def test_earlier_on_time_check_in_clears_lateness(self):
        """Birinchi kelish vaqtida bo'lsa, avvalgi kechikish yozuvi olib tashlanadi."""
        d = date(2026, 6, 2)  # Tuesday
        late_ts = self._aware(d, time(9, 30))
        early_ts = self._aware(d, time(8, 55))
        AttendanceLog.objects.create(
            employee=self.emp,
            event_type="check_in",
            timestamp=late_ts,
            source_id="late_only",
            source="device",
        )
        recompute_daily_summary(self.emp, d)
        self.assertTrue(LatenessRecord.objects.filter(employee=self.emp, date=d).exists())
        AttendanceLog.objects.create(
            employee=self.emp,
            event_type="check_in",
            timestamp=early_ts,
            source_id="early_ok",
            source="device",
        )
        recompute_daily_summary(self.emp, d)
        self.assertFalse(LatenessRecord.objects.filter(employee=self.emp, date=d).exists())
        s = DailySummary.objects.get(employee=self.emp, date=d)
        self.assertEqual(s.status, DailySummary.STATUS_PRESENT)
        self.assertEqual(s.minutes_late, 0)

    def test_no_check_in_deletes_stale_lateness(self):
        d = date(2026, 6, 3)
        LatenessRecord.objects.create(
            employee=self.emp,
            date=d,
            minutes_late=10,
            check_in_time=self._aware(d, time(9, 20)),
            expected_start=time(9, 0),
        )
        recompute_daily_summary(self.emp, d)
        self.assertFalse(LatenessRecord.objects.filter(employee=self.emp, date=d).exists())

    def test_non_working_day_clears_lateness(self):
        sched = WorkSchedule.objects.create(
            name="Du-Ju",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0),
            grace_period_minutes=5,
            working_days="0,1,2,3,4",
        )
        self.emp.work_schedule = sched
        self.emp.save(update_fields=["work_schedule"])
        # 2026-06-06 = Saturday (weekday 5)
        d = date(2026, 6, 6)
        LatenessRecord.objects.create(
            employee=self.emp,
            date=d,
            minutes_late=5,
            check_in_time=self._aware(d, time(10, 0)),
            expected_start=time(9, 0),
        )
        AttendanceLog.objects.create(
            employee=self.emp,
            event_type="check_in",
            timestamp=self._aware(d, time(10, 0)),
            source_id="sat_in",
            source="device",
        )
        recompute_daily_summary(self.emp, d)
        self.assertFalse(LatenessRecord.objects.filter(employee=self.emp, date=d).exists())
        s = DailySummary.objects.get(employee=self.emp, date=d)
        self.assertEqual(s.status, DailySummary.STATUS_PRESENT)
