"""
Celery tasks: end-of-day summary and penalty application.
Jarima va hisobotlar ish kuni tugagach (masalan 20:00) bir marta hisoblanadi.
"""
import logging
from datetime import date

from celery import shared_task
from django.utils import timezone

from employees.models import Employee
from attendance.services import recompute_daily_summary
from attendance.models import LatenessRecord
from penalties.services import apply_penalty_for_lateness
from notifications.tasks import send_telegram_message

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_daily_summary_and_penalties(self, day=None):
    """
    Kun oxirida barcha xodimlar uchun kunlik xulosa qayta hisoblash va
    kechikish bo'yicha jarimalarni bir marta qo'llash.
    Birinchi kelish (first check_in) va oxirgi ketish (last check_out) ishlatiladi.
    day: sana (YYYY-MM-DD yoki date); berilmasa bugungi sana.
    """
    if day is None:
        day = timezone.now().date()
    elif isinstance(day, str):
        day = date.fromisoformat(day)

    # Barcha faol xodimlar uchun kunlik xulosa qayta hisobla
    employees = Employee.objects.filter(is_active=True)
    employees_count = employees.count()
    for employee in employees:
        try:
            recompute_daily_summary(employee, day)
        except Exception as e:
            logger.exception("run_daily_summary_and_penalties recompute employee=%s day=%s: %s", employee.pk, day, e)

    # Shu kun uchun kechikish yozuvlari bo'yicha jarima qo'llash (har biri uchun bitta)
    lateness_records = list(LatenessRecord.objects.filter(date=day).select_related("employee"))
    for lateness in lateness_records:
        try:
            penalty = apply_penalty_for_lateness(lateness)
            if penalty:
                emp = lateness.employee
                name = emp.get_full_name()
                date_str = getattr(penalty, "penalty_date", day)
                if getattr(penalty, "penalty_percent", None) is not None:
                    msg_lines = [
                        f"📅 Sana: {date_str}",
                        f"⏰ Kechikish: {name} (ID: {emp.employee_id}) — {lateness.minutes_late} daqiqa kechikdi.",
                        f"💰 Jarima: oylikdan {penalty.penalty_percent}%.",
                    ]
                else:
                    msg_lines = [
                        f"📅 Sana: {date_str}",
                        f"⏰ Kechikish: {name} (ID: {emp.employee_id}) — {lateness.minutes_late} daqiqa kechikdi.",
                        f"💰 Jarima: {penalty.amount} so'm.",
                    ]
                if getattr(emp, "telegram_username", None) and str(emp.telegram_username).strip():
                    username = str(emp.telegram_username).strip().lstrip("@")
                    msg_lines.append(f"@{username}")
                send_telegram_message.delay("\n".join(msg_lines))
        except Exception as e:
            logger.exception("run_daily_summary_and_penalties penalty lateness=%s: %s", lateness.pk, e)

    return {"ok": True, "day": str(day), "employees": employees_count, "lateness_count": len(lateness_records)}
