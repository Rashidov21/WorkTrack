"""Apply penalty from active rule for a lateness record."""
from decimal import Decimal
from django.utils import timezone

from .models import PenaltyRule, Penalty


def apply_penalty_for_lateness(lateness_record):
    """
    Apply penalty for a lateness record using first active rule (per_minute or fixed).
    Returns created Penalty or None.
    """
    rule = PenaltyRule.objects.filter(is_active=True).first()
    if not rule:
        return None

    if rule.rule_type == "per_minute":
        amount = Decimal(lateness_record.minutes_late) * rule.amount_per_unit
    elif rule.rule_type == "fixed":
        amount = rule.amount_per_unit
    else:
        amount = rule.amount_per_unit

    if amount <= 0:
        return None

    # Avoid duplicate penalty for the same lateness
    if Penalty.objects.filter(lateness_record=lateness_record).exists():
        return None

    penalty = Penalty.objects.create(
        employee=lateness_record.employee,
        amount=amount,
        rule=rule,
        lateness_record=lateness_record,
        reason=f"Late {lateness_record.minutes_late} min on {lateness_record.date}",
        is_manual=False,
    )
    return penalty
