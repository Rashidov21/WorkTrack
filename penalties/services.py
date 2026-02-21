"""Apply penalty from active rule for a lateness record."""
from decimal import Decimal
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import Sum

from .models import PenaltyRule, Penalty, PenaltyExemption


def is_penalty_exempt(employee, date):
    """Shu xodim va sana uchun jarimadan ozod bormi."""
    return PenaltyExemption.objects.filter(
        employee=employee,
        date_from__lte=date,
        date_to__gte=date,
    ).exists()


def apply_penalty_for_lateness(lateness_record):
    """
    Apply penalty for a lateness record using first active rule (per_minute or fixed).
    Kunlik maksimum (max_amount_per_day) dan oshmasligi uchun cheklanadi.
    Sababli (ta'til, kasallik, ruxsat) ozod bo'lgan kunlarda jarima yozilmaydi.
    Returns created Penalty or None.
    """
    rule = PenaltyRule.objects.filter(is_active=True).first()
    if not rule:
        return None

    # Avoid duplicate penalty for the same lateness
    if Penalty.objects.filter(lateness_record=lateness_record).exists():
        return None

    # Sababli jarima yozilmasin: shu kun uchun ozod mavjud bo'lsa
    if is_penalty_exempt(lateness_record.employee, lateness_record.date):
        return None

    # Oylikdan foiz: faqat foiz yoziladi (1% yoki 2%), summa buqalter oy oxirida hisoblaydi
    if rule.rule_type == "percent_of_salary":
        threshold = int(rule.threshold_minutes) if rule.threshold_minutes else 30
        if lateness_record.minutes_late <= threshold:
            penalty_percent = rule.percent_if_late_le_threshold or Decimal("1")
        else:
            penalty_percent = rule.percent_if_late_gt_threshold or Decimal("2")
        penalty = Penalty.objects.create(
            employee=lateness_record.employee,
            amount=Decimal("0"),
            penalty_percent=penalty_percent,
            rule=rule,
            lateness_record=lateness_record,
            penalty_date=lateness_record.date,
            reason=_("Kechikish %(min)s daq — oylikdan %(p)s%%") % {"min": lateness_record.minutes_late, "p": penalty_percent},
            is_manual=False,
        )
        return penalty

    if rule.rule_type == "per_minute":
        amount = Decimal(lateness_record.minutes_late) * rule.amount_per_unit
    elif rule.rule_type == "fixed":
        amount = rule.amount_per_unit
    else:
        amount = rule.amount_per_unit or Decimal("0")

    if amount <= 0:
        return None

    if rule.max_amount_per_day is not None and rule.max_amount_per_day > 0:
        existing_total = (
            Penalty.objects.filter(
                employee=lateness_record.employee,
                penalty_date=lateness_record.date,
            ).aggregate(s=Sum("amount"))["s"]
            or Decimal("0")
        )
        remaining = rule.max_amount_per_day - existing_total
        if remaining <= 0:
            return None
        amount = min(amount, remaining)

    penalty = Penalty.objects.create(
        employee=lateness_record.employee,
        amount=amount,
        rule=rule,
        lateness_record=lateness_record,
        penalty_date=lateness_record.date,
        reason=_("Late %(min)s min on %(date)s") % {"min": lateness_record.minutes_late, "date": lateness_record.date},
        is_manual=False,
    )
    return penalty
