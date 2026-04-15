"""Penalty rules and penalty records."""
from datetime import date
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PenaltyRule(models.Model):
    """Admin-defined rule: per-minute, fixed, percent of salary, or custom."""
    RULE_TYPES = [
        ("per_minute", _("Har daqiqaga")),
        ("fixed", _("Qat'iy summa")),
        ("percent_of_salary", _("Oylikdan foiz")),
        ("custom", _("Boshqa")),
    ]
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, default="per_minute")
    # For per_minute: amount per minute late; for fixed: fixed amount
    amount_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True,
        help_text="Per minute (per_minute) or fixed amount (fixed). Oylikdan foiz uchun ishlatilmaydi.",
    )
    # Oylikdan foiz: shu daqiqagacha 1%, undan keyin 2%
    threshold_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Chegara (daq)"),
        help_text=_("Oylikdan foiz: shu daqiqagacha birinchi foiz, undan keyin ikkinchi foiz qo'llanadi."),
    )
    percent_if_late_le_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1,
        verbose_name=_("Foiz (≤ chegara)"),
        help_text=_("Kechikish chegara daqiqagacha bo'lsa (masalan 1 = 1%)."),
    )
    percent_if_late_gt_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2,
        verbose_name=_("Foiz (> chegara)"),
        help_text=_("Kechikish chegaradan oshsa (masalan 2 = 2%)."),
    )
    max_amount_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=50000,
        verbose_name=_("Kunlik maksimum (so'm)"),
        help_text=_("Bir xodim uchun shu kundagi jami jarima shu summandan oshmasin. Bo'sh qoldirilsa cheklov yo'q."),
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Bo'lim"),
        help_text=_(
            "Bo'sh qoldiring — barcha bo'limlar uchun umumiy qoida. To'ldiring — faqat shu nomdagi bo'lim "
            "(xodim kartasidagi bo'lim bilan mos kelishi kerak). Bir vaqtda bir bo'lim uchun bitta faol qoida."
        ),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Penalty Rule")
        verbose_name_plural = _("Penalty Rules")

    def clean(self):
        super().clean()
        dept = (self.department or "").strip()
        self.department = dept or None
        if not self.is_active:
            return
        qs = PenaltyRule.objects.filter(is_active=True)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if self.department:
            if qs.filter(department__iexact=self.department).exists():
                raise ValidationError(
                    {
                        "department": _(
                            "Bu bo'lim uchun allaqachon boshqa faol qoida bor. Faqat bittasini faol qiling yoki "
                            "oldingi qoidani o'chiring."
                        )
                    }
                )
        else:
            if qs.filter(Q(department__isnull=True) | Q(department="")).exists():
                raise ValidationError(
                    {
                        "department": _(
                            "Umumiy (bo'sh bo'lim) faol qoida allaqachon mavjud. Bir vaqtda bitta umumiy faol qoida bo'lishi kerak."
                        )
                    }
                )

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class Penalty(models.Model):
    """Applied penalty for an employee (linked to lateness or manual)."""
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="penalties",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Oylikdan foiz qoidasida: 1 yoki 2 (%), buqalter oy oxirida yig'adi
    penalty_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Jarima foizi (%)"),
    )
    rule = models.ForeignKey(
        PenaltyRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="penalties",
    )
    # Link to lateness or leave as reference
    lateness_record = models.ForeignKey(
        "attendance.LatenessRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="penalties",
    )
    reason = models.CharField(max_length=255, blank=True)
    is_manual = models.BooleanField(default=False)
    penalty_date = models.DateField(
        default=date.today,
        verbose_name=_("Jarima sanasi"),
        help_text=_("Jarima qaysi kun uchun (davomat o'tgan sana)."),
    )
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_penalties",
    )

    class Meta:
        ordering = ["-penalty_date", "-created_at"]
        verbose_name = _("Penalty")
        verbose_name_plural = _("Penalties")

    def __str__(self):
        return f"{self.employee} {self.amount} @ {self.penalty_date}"


class PenaltyExemption(models.Model):
    """Xodimning ma'lum sana(lar) uchun jarimadan ozod qilinishi (ta'til, kasallik, ruxsat)."""
    REASON_CHOICES = [
        ("sick_leave", _("Kasallik (bolnich)")),
        ("leave_approved", _("Ishdan ruxsat tasdiqlangan")),
        ("business_trip", _("Ish safari")),
        ("other", _("Boshqa")),
    ]
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="penalty_exemptions",
    )
    date_from = models.DateField(verbose_name=_("Dan"))
    date_to = models.DateField(
        verbose_name=_("Gacha"),
        help_text=_("Bir kun uchun Dan = Gacha qiling."),
    )
    reason_type = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default="other",
        verbose_name=_("Sabab"),
    )
    reason_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Izoh"),
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_penalty_exemptions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_from"]
        verbose_name = _("Jarimadan ozod")
        verbose_name_plural = _("Jarimadan ozodlar")

    def __str__(self):
        return f"{self.employee} {self.date_from}–{self.date_to} ({self.get_reason_type_display()})"


class PenaltyDecisionLog(models.Model):
    """Audit trail: why auto-penalty was created or skipped."""

    DECISION_CREATED = "created"
    DECISION_SKIPPED = "skipped"
    DECISION_ERROR = "error"

    DECISION_CHOICES = [
        (DECISION_CREATED, _("Yaratildi")),
        (DECISION_SKIPPED, _("O'tkazib yuborildi")),
        (DECISION_ERROR, _("Xatolik")),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="penalty_decision_logs",
    )
    lateness_record = models.ForeignKey(
        "attendance.LatenessRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_logs",
    )
    date = models.DateField(db_index=True)
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, db_index=True)
    reason_code = models.CharField(max_length=64, db_index=True)
    details = models.TextField(blank=True)
    penalty = models.ForeignKey(
        Penalty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decision_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Jarima qaror logi")
        verbose_name_plural = _("Jarima qaror loglari")

    def __str__(self):
        return f"{self.employee} {self.date} {self.decision}:{self.reason_code}"
