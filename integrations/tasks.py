"""
Celery tasks: process device webhook event (save log, recompute summary).
Jarima kun oxirida run_daily_summary_and_penalties taskida (masalan 20:00) qo'llanadi.
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta

from attendance.services import create_log_idempotent, recompute_daily_summary
from .hikvision_client import HikvisionClient
from .models import RawDeviceEvent, DeviceImportJob, IntegrationSettings

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


@shared_task(bind=True, max_retries=3)
def process_raw_device_event(self, raw_event_id: int):
    """
    Process one stored RawDeviceEvent end-to-end.
    Raw event is always persisted first at webhook ingress.
    """
    raw_event = RawDeviceEvent.objects.filter(pk=raw_event_id).first()
    if not raw_event:
        return {"ok": False, "reason": "raw_event_not_found"}

    payload = raw_event.payload_json or {}
    result = process_device_event(payload)

    raw_event.retry_count = max(raw_event.retry_count, self.request.retries)
    raw_event.processed_at = timezone.now()
    if result.get("ok"):
        raw_event.status = RawDeviceEvent.STATUS_PROCESSED
        raw_event.error_code = ""
        raw_event.error_message = ""
    elif result.get("reason") == "employee_not_found":
        raw_event.status = RawDeviceEvent.STATUS_UNMATCHED
        raw_event.error_code = "employee_not_found"
        raw_event.error_message = "Employee mapping not found for incoming event."
    else:
        raw_event.status = RawDeviceEvent.STATUS_FAILED
        raw_event.error_code = result.get("reason", "processing_failed")
        raw_event.error_message = str(result)
    raw_event.save(
        update_fields=[
            "retry_count",
            "processed_at",
            "status",
            "error_code",
            "error_message",
        ]
    )
    return {"ok": True, "raw_event_id": raw_event.pk, "status": raw_event.status}


def _acs_item_to_payload(item: dict):
    """Map one Hikvision AcsEvent InfoList item to internal payload."""
    ts = item.get("time") or ""
    employee_id = (
        item.get("employeeNoString")
        or item.get("personId")
        or item.get("cardNo")
        or ""
    )
    label = str(item.get("label") or "").lower()
    verify_mode = str(item.get("currentVerifyMode") or "").lower()
    minor = item.get("minor")
    event_type = "check_in"
    if "out" in label or minor in (1025, 2049):
        event_type = "check_out"
    elif "in" in label or minor in (1024, 2048):
        event_type = "check_in"
    elif "exit" in verify_mode:
        event_type = "check_out"
    source_id = str(item.get("serialNo") or item.get("event_id") or "").strip()
    return {
        "employee_id": str(employee_id).strip(),
        "event_type": event_type,
        "timestamp": ts,
        "event_id": source_id,
    }


@shared_task(bind=True, max_retries=2)
def run_device_import_job(self, job_id: int):
    """Run historical import job by pulling events from Hikvision API."""
    job = DeviceImportJob.objects.filter(pk=job_id).first()
    if not job:
        return {"ok": False, "reason": "job_not_found"}

    settings = IntegrationSettings.get_settings()
    if not settings.device_ip or not settings.api_username or not settings.api_password:
        job.status = DeviceImportJob.STATUS_FAILED
        job.error_message = "Device API settings are incomplete."
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
        return {"ok": False, "reason": "invalid_device_settings"}

    base_url = settings.device_ip.strip()
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = f"http://{base_url}"
    client = HikvisionClient(base_url=base_url, username=settings.api_username, password=settings.api_password)

    job.status = DeviceImportJob.STATUS_RUNNING
    job.started_at = timezone.now()
    job.error_message = ""
    job.save(update_fields=["status", "started_at", "error_message"])

    position = 0
    page_size = 30
    fetched = 0
    queued = 0
    failed = 0

    try:
        while True:
            result = client.fetch_events_page(
                date_from=job.date_from,
                date_to=job.date_to,
                position=position,
                max_results=page_size,
            )
            acs = result.get("AcsEvent", {}) if isinstance(result, dict) else {}
            items = acs.get("InfoList") or []
            if not isinstance(items, list):
                items = []

            num_matches = int(acs.get("numOfMatches") or len(items) or 0)
            if num_matches == 0 and not items:
                break

            for item in items:
                try:
                    payload = _acs_item_to_payload(item if isinstance(item, dict) else {})
                    raw_event = RawDeviceEvent.objects.create(
                        device_ip=settings.device_ip,
                        external_event_id=str(payload.get("event_id") or ""),
                        payload_json=payload,
                    )
                    process_raw_device_event.delay(raw_event.pk)
                    queued += 1
                except Exception:
                    failed += 1
            fetched += len(items)
            position += num_matches if num_matches else len(items)
            job.last_cursor = position
            job.fetched_count = fetched
            job.queued_count = queued
            job.failed_count = failed
            job.save(update_fields=["last_cursor", "fetched_count", "queued_count", "failed_count"])

            status_flag = str(acs.get("responseStatusStrg") or "").upper()
            total_matches = acs.get("totalMatches")
            if status_flag not in ("MORE",) and len(items) < page_size:
                break
            if total_matches is not None and position >= int(total_matches):
                break

        # Importdan keyin shu oraliqni qayta hisoblash (attendance + penalties).
        from attendance.tasks import run_daily_summary_and_penalties
        d = job.date_from
        while d <= job.date_to:
            run_daily_summary_and_penalties.delay(d.isoformat())
            d += timedelta(days=1)

        job.status = DeviceImportJob.STATUS_SUCCESS
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "finished_at"])
        return {"ok": True, "job_id": job.pk, "fetched": fetched, "queued": queued, "failed": failed}
    except Exception as exc:
        job.status = DeviceImportJob.STATUS_FAILED
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
        raise
