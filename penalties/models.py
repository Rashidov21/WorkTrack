"""Penalty rules and penalty records."""
from django.db import models
from django.utils import timezone


class PenaltyRule(models.Model):
    """Admin-defined rule: per-minute, fixed, or custom."""
    RULE_TYPES = [
        ("per_minute", "Per Minute Late"),
        ("fixed", "Fixed Amount"),
        ("custom", "Custom"),
    ]
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, default="per_minute")
    # For per_minute: amount per minute late
    amount_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Per minute (per_minute) or fixed amount (fixed)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Penalty Rule"
        verbose_name_plural = "Penalty Rules"

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
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_penalties",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Penalty"
        verbose_name_plural = "Penalties"

    def __str__(self):
        return f"{self.employee} {self.amount} @ {self.created_at.date()}"
