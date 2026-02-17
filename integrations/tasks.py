"""
Celery tasks: process device webhook event (save log, recompute summary).
Jarima kun oxirida run_daily_summary_and_penalties taskida (masalan 20:00) qo'llanadi.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import date

from attendance.services import create_log_idempotent, recompute_daily_summary

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_device_event(self, payload: dict):
    """
    Idempotent processing of one device event.
    Log yoziladi, kunlik xulosa qayta hisoblanadi (birinchi kelish / oxirgi ketish).
    Jarima va Telegram xabarlari kun oxirida run_daily_summary_and_penalties da bajariladi.
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
        logger.warning(
            "process_device_event: employee_not_found employee_id=%s",
            repr(employee_id),
        )
        return {"ok": False, "reason": "employee_not_found"}

    day = log.timestamp.date() if hasattr(log.timestamp, "date") else date.fromisoformat(str(log.timestamp)[:10])
    recompute_daily_summary(log.employee, day)

    return {"ok": True, "created": created, "log_id": log.pk}
