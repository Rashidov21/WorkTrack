"""
Oxirgi 7 kun uchun kunlik xulosa va jarimalarni hisoblash.
Celery kerak emas — to'g'ridan-to'gri Telegram jo'natiladi.

Ishlatish:
  python manage.py run_weekly_penalties
  python manage.py run_weekly_penalties --days 14
  python manage.py run_weekly_penalties --dry-run
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from employees.models import Employee
from attendance.services import recompute_daily_summary
from attendance.models import LatenessRecord
from penalties.services import apply_penalty_for_lateness
from notifications.services import send_telegram_message_sync


class Command(BaseCommand):
    help = "Oxirgi 7 kun uchun xulosa va jarimalarni hisoblaydi, Telegram sync jo'natadi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Nechi kun orqaga hisoblash (default: 7)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Jarima yozmasdan va Telegram jo'natmasdan faqat xulosa hisobla",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)

        self.stdout.write(f"Oraliq: {start_date} — {end_date} (dry_run={dry_run})")

        for day_offset in range(days):
            day_date = start_date + timedelta(days=day_offset)
            self._process_day(day_date, dry_run)

        self.stdout.write(self.style.SUCCESS("Tugadi."))

    def _process_day(self, day_date: date, dry_run: bool):
        # 1) Kunlik xulosa (LatenessRecord yaratiladi/yangilanadi)
        employees = Employee.objects.filter(is_active=True)
        for employee in employees:
            try:
                recompute_daily_summary(employee, day_date)
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(f"  recompute employee={employee.pk} {day_date}: {e}")
                )

        if dry_run:
            self.stdout.write(f"  {day_date}: xulosa hisoblandi (dry-run, jarima o‘chirildi)")
            return

        # 2) Shu kun uchun kechikishlar bo'yicha jarima + Telegram
        lateness_records = LatenessRecord.objects.filter(date=day_date).select_related("employee")
        sent = 0
        for lateness in lateness_records:
            try:
                penalty = apply_penalty_for_lateness(lateness)
                if not penalty:
                    continue
                emp = lateness.employee
                name = emp.get_full_name()
                date_str = getattr(penalty, "penalty_date", day_date)
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
                result = send_telegram_message_sync("\n".join(msg_lines))
                if result.get("ok"):
                    sent += 1
                else:
                    self.stderr.write(
                        self.style.WARNING(f"  Telegram {emp.employee_id}: {result.get('reason') or result.get('error')}")
                    )
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"  penalty lateness {lateness.pk}: {e}"))

        self.stdout.write(f"  {day_date}: {len(lateness_records)} kechikish, {sent} xabar jo‘natildi.")
