"""
Celery tasks: process device webhook event (save log, recompute summary, apply penalty, notify).
"""
from celery import shared_task
from django.utils import timezone
from datetime import date

from attendance.services import create_log_idempotent, recompute_daily_summary
from attendance.models import DailySummary, LatenessRecord
from penalties.services import apply_penalty_for_lateness
from notifications.tasks import send_telegram_message


@shared_task(bind=True, max_retries=3)
def process_device_event(self, payload: dict):
    """
    Idempotent processing of one device event.
    payload: { "employee_id": "...", "event_type": "check_in"|"check_out", "timestamp": "ISO", "event_id": "..." }
    """
    employee_id = payload.get("employee_id") or payload.get("person_id") or payload.get("card_no")
    event_type = payload.get("event_type", "").lower().replace(" ", "_")
    if event_type not in ("check_in", "check_out"):
        event_type = "check_in" if payload.get("attendance_status") in (1, "in", "check_in") else "check_out"
    timestamp = payload.get("timestamp") or timezone.now().isoformat()
    source_id = payload.get("event_id") or payload.get("serial_no") or payload.get("id") or ""

    log, created = create_log_idempotent(
        employee_id=str(employee_id),
        event_type=event_type,
        timestamp=timestamp,
        source_id=str(source_id) if source_id else "",
        source="device",
    )
    if not log:
        return {"ok": False, "reason": "employee_not_found"}

    day = log.timestamp.date() if hasattr(log.timestamp, "date") else date.fromisoformat(str(log.timestamp)[:10])
    recompute_daily_summary(log.employee, day)

    # If we just recorded a lateness (today, this employee), apply penalty and notify
    summary = DailySummary.objects.filter(employee=log.employee, date=day).first()
    if summary and summary.status == DailySummary.STATUS_LATE and summary.minutes_late > 0:
        lateness = LatenessRecord.objects.filter(employee=log.employee, date=day).first()
        if lateness:
            penalty = apply_penalty_for_lateness(lateness)
            if penalty:
                send_telegram_message.delay(
                    f"⚠️ Late: {log.employee.get_full_name()} ({log.employee.employee_id}) — {summary.minutes_late} min late. Penalty: {penalty.amount}"
                )
    return {"ok": True, "created": created, "log_id": log.pk}
