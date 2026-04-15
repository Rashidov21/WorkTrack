"""Apply penalty from active rule for a lateness record."""
from decimal import Decimal
from django.db.models import Q, Sum
from django.utils.translation import gettext as _

from .models import PenaltyRule, Penalty, PenaltyExemption, PenaltyDecisionLog


def is_penalty_exempt(employee, date):
    """Shu xodim va sana uchun jarimadan ozod bormi."""
    return PenaltyExemption.objects.filter(
        employee=employee,
        date_from__lte=date,
        date_to__gte=date,
    ).exists()


def resolve_penalty_rule_for_employee(employee):
    """
    Faol qoida: avvalo xodim bo'limi bo'yicha, yo'q bo'lsa umumiy (department bo'sh).
    Mos qoida bo'lmasa None — avtomatik jarima yozilmaydi (qo'lda jarima mumkin).
    """
    dept = (getattr(employee, "department", None) or "").strip()
    if dept:
        rule = (
            PenaltyRule.objects.filter(is_active=True, department__iexact=dept)
            .order_by("pk")
            .first()
        )
        if rule:
            return rule
    return (
        PenaltyRule.objects.filter(is_active=True)
        .filter(Q(department__isnull=True) | Q(department=""))
        .order_by("pk")
        .first()
    )


def apply_penalty_for_lateness(lateness_record):
    """
    Apply penalty for a lateness record using resolved active rule for employee's department (or global).
    Kunlik maksimum (max_amount_per_day) dan oshmasligi uchun cheklanadi.
    Sababli (ta'til, kasallik, ruxsat) ozod bo'lgan kunlarda jarima yozilmaydi.
    Returns created Penalty or None.
    """
    rule = resolve_penalty_rule_for_employee(lateness_record.employee)
    if not rule:
        PenaltyDecisionLog.objects.create(
            employee=lateness_record.employee,
            lateness_record=lateness_record,
            date=lateness_record.date,
            decision=PenaltyDecisionLog.DECISION_SKIPPED,
            reason_code="no_active_rule",
            details="No active rule found for employee department/global.",
        )
        return None

    # Avoid duplicate penalty for the same lateness
    if Penalty.objects.filter(lateness_record=lateness_record).exists():
        PenaltyDecisionLog.objects.create(
            employee=lateness_record.employee,
            lateness_record=lateness_record,
            date=lateness_record.date,
            decision=PenaltyDecisionLog.DECISION_SKIPPED,
            reason_code="already_penalized",
            details="Penalty already exists for this lateness record.",
        )
        return None

    # Sababli jarima yozilmasin: shu kun uchun ozod mavjud bo'lsa
    if is_penalty_exempt(lateness_record.employee, lateness_record.date):
        PenaltyDecisionLog.objects.create(
            employee=lateness_record.employee,
            lateness_record=lateness_record,
            date=lateness_record.date,
            decision=PenaltyDecisionLog.DECISION_SKIPPED,
            reason_code="penalty_exempt",
            details="Employee has penalty exemption for this date.",
        )
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
        PenaltyDecisionLog.objects.create(
            employee=lateness_record.employee,
            lateness_record=lateness_record,
            date=lateness_record.date,
            decision=PenaltyDecisionLog.DECISION_CREATED,
            reason_code="percent_of_salary",
            details=f"Created percent penalty {penalty_percent}%.",
            penalty=penalty,
        )
        return penalty

    if rule.rule_type == "per_minute":
        amount = Decimal(lateness_record.minutes_late) * rule.amount_per_unit
    elif rule.rule_type == "fixed":
        amount = rule.amount_per_unit
    else:
        amount = rule.amount_per_unit or Decimal("0")

    if amount <= 0:
        PenaltyDecisionLog.objects.create(
            employee=lateness_record.employee,
            lateness_record=lateness_record,
            date=lateness_record.date,
            decision=PenaltyDecisionLog.DECISION_SKIPPED,
            reason_code="non_positive_amount",
            details=f"Computed amount is non-positive: {amount}.",
        )
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
            PenaltyDecisionLog.objects.create(
                employee=lateness_record.employee,
                lateness_record=lateness_record,
                date=lateness_record.date,
                decision=PenaltyDecisionLog.DECISION_SKIPPED,
                reason_code="daily_cap_reached",
                details=f"Remaining daily cap is {remaining}.",
            )
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
    PenaltyDecisionLog.objects.create(
        employee=lateness_record.employee,
        lateness_record=lateness_record,
        date=lateness_record.date,
        decision=PenaltyDecisionLog.DECISION_CREATED,
        reason_code="amount_penalty",
        details=f"Created amount penalty {amount}.",
        penalty=penalty,
    )
    return penalty
