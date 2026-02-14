"""
Business logic: process attendance events, compute daily summary, lateness.
"""
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db import transaction

from employees.models import Employee
from .models import AttendanceLog, DailySummary, LatenessRecord


def get_employee_by_identifier(employee_id: str = None, device_person_id: str = None):
    """Resolve employee by employee_id or device_person_id."""
    if employee_id:
        return Employee.objects.filter(employee_id=employee_id, is_active=True).first()
    if device_person_id:
        return Employee.objects.filter(device_person_id=device_person_id, is_active=True).first()
    return None


def create_log_idempotent(employee_id: str, event_type: str, timestamp, source_id: str = "", source: str = "device"):
    """
    Create attendance log if not already present (idempotent by source_id).
    Returns (log, created).
    """
    employee = get_employee_by_identifier(employee_id=employee_id)
    if not employee:
        return None, False

    if source_id and AttendanceLog.objects.filter(source_id=source_id).exists():
        return AttendanceLog.objects.get(source_id=source_id), False

    if isinstance(timestamp, (str,)):
        timestamp = timezone.make_aware(datetime.fromisoformat(timestamp.replace("Z", "+00:00")))
    elif timestamp and timezone.is_naive(timestamp):
        timestamp = timezone.make_aware(timestamp)

    log = AttendanceLog.objects.create(
        employee=employee,
        event_type=event_type,
        timestamp=timestamp,
        source_id=source_id or "",
        source=source,
    )
    return log, True


def recompute_daily_summary(employee, day: date):
    """Build or update DailySummary and LatenessRecord for one employee for one day."""
    logs = (
        AttendanceLog.objects.filter(employee=employee, timestamp__date=day)
        .order_by("timestamp")
    )
    check_in = logs.filter(event_type="check_in").first()
    check_out = logs.filter(event_type="check_out").last()

    summary, _ = DailySummary.objects.update_or_create(
        employee=employee,
        date=day,
        defaults={
            "check_in_time": check_in.timestamp if check_in else None,
            "check_out_time": check_out.timestamp if check_out else None,
            "missing_check_out": check_in and not check_out,
            "working_minutes": 0,
            "minutes_late": 0,
            "status": DailySummary.STATUS_ABSENT,
        },
    )

    if not check_in:
        summary.save()
        return summary

    # Working minutes
    if check_in and check_out:
        delta = check_out.timestamp - check_in.timestamp
        summary.working_minutes = int(delta.total_seconds() / 60)
    summary.missing_check_out = bool(check_in and not check_out)

    # Lateness: use work schedule for this day if set
    work_start, work_end, grace_minutes, is_working_day = employee.get_work_params_for_date(day)
    if is_working_day:
        start_dt = timezone.make_aware(datetime.combine(day, work_start))
        grace_end = start_dt + timedelta(minutes=grace_minutes)
        if check_in.timestamp > grace_end:
            minutes_late = int((check_in.timestamp - grace_end).total_seconds() / 60)
            summary.minutes_late = minutes_late
            summary.status = DailySummary.STATUS_LATE
            LatenessRecord.objects.update_or_create(
                employee=employee,
                date=day,
                defaults={
                    "minutes_late": minutes_late,
                    "check_in_time": check_in.timestamp,
                    "expected_start": work_start,
                },
            )
        else:
            summary.status = DailySummary.STATUS_PRESENT
    else:
        # Dam olish kuni — kechikish hisoblanmaydi
        summary.status = DailySummary.STATUS_PRESENT

    summary.save()
    return summary
