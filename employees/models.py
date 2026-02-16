"""Employee model: ID, department, work times, grace period, active status."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class WorkSchedule(models.Model):
    """
    Ish grafigi: vaqtlar va ish kunlari.
    Xodimga tayinlansa, kechikish/jarima shu grafik bo‘yicha hisoblanadi.
    """
    name = models.CharField(max_length=100, verbose_name=_("Nomi"))
    work_start_time = models.TimeField(verbose_name=_("Ish boshlanish vaqti"))
    work_end_time = models.TimeField(verbose_name=_("Ish tugash vaqti"))
    grace_period_minutes = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Ruxsat etilgan muhlat (daqika)"),
        help_text=_("Ish boshlanish vaqtidan keyin shuncha daqiqa kechikishga ruxsat"),
    )
    # 0=Dushanba, 1=Seshanba, ..., 6=Yakshanba (Python weekday)
    working_days = models.CharField(
        max_length=20,
        default="0,1,2,3,4",
        help_text=_("Ish kunlari: vergul bilan ajratilgan (0=Du..6=Ya). Masalan 0,1,2,3,4 = Du-Ju"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Ish grafigi")
        verbose_name_plural = _("Ish grafiklari")

    def __str__(self):
        return self.name

    def get_working_weekdays(self):
        """Return set of weekday integers (0-6) when employee should work."""
        if not self.working_days:
            return set(range(7))
        return set(int(x.strip()) for x in self.working_days.split(",") if x.strip().isdigit())

    def is_working_day(self, date):
        """date is a date object; Python weekday: Monday=0, Sunday=6."""
        return date.weekday() in self.get_working_weekdays()


class Employee(models.Model):
    """Employee master data for attendance and penalties."""
    employee_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    # Optional: ish grafigi. Agar berilmasa, quyidagi vaqtlar ishlatiladi
    work_schedule = models.ForeignKey(
        "employees.WorkSchedule",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
        verbose_name=_("Ish grafigi"),
    )
    work_start_time = models.TimeField(help_text=_("Ish boshlanish (grafik tanlanmasa ishlatiladi)"))
    work_end_time = models.TimeField(help_text=_("Ish tugash (grafik tanlanmasa ishlatiladi)"))
    grace_period_minutes = models.PositiveIntegerField(
        default=5,
        help_text=_("Ruxsat etilgan muhlat daqiqada (grafik tanlanmasa ishlatiladi)"),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Optional: Hikvision person ID for device matching
    device_person_id = models.CharField(max_length=100, blank=True)
    # Optional: Telegram username for notifications (without @); bot will tag in group
    telegram_username = models.CharField(max_length=100, blank=True, verbose_name=_("Telegram username (ixtiyoriy)"))

    class Meta:
        ordering = ["employee_id"]
        verbose_name = _("Xodim")
        verbose_name_plural = _("Xodimlar")

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_work_params_for_date(self, day):
        """
        Berilgan sana uchun ish vaqti va muhlatni qaytaradi.
        Returns: (work_start_time, work_end_time, grace_period_minutes, is_working_day).
        Agar xodimda ish grafigi tayinlangan va bu kun grafikda ish kuni bo‘lsa — grafikdagi vaqtlar.
        Aks holda — xodimning o‘z vaqtlari; ish grafigi bo‘yicha bu kun ish kuni emas bo‘lsa is_working_day=False.
        """
        if self.work_schedule and self.work_schedule.is_active:
            s = self.work_schedule
            is_working = s.is_working_day(day)
            return (s.work_start_time, s.work_end_time, s.grace_period_minutes, is_working)
        return (
            self.work_start_time,
            self.work_end_time,
            self.grace_period_minutes,
            True,
        )
