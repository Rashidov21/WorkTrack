from django.contrib import admin
from .models import PenaltyRule, Penalty, PenaltyExemption, PenaltyDecisionLog


@admin.register(PenaltyRule)
class PenaltyRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "department", "rule_type", "amount_per_unit", "is_active"]
    list_filter = ["is_active"]


@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ["employee", "amount", "rule", "is_manual", "created_at"]
    list_filter = ["is_manual"]
    date_hierarchy = "created_at"


@admin.register(PenaltyExemption)
class PenaltyExemptionAdmin(admin.ModelAdmin):
    list_display = ["employee", "date_from", "date_to", "reason_type", "created_at"]
    list_filter = ["reason_type"]
    date_hierarchy = "date_from"


@admin.register(PenaltyDecisionLog)
class PenaltyDecisionLogAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "decision", "reason_code", "penalty", "created_at"]
    list_filter = ["decision", "reason_code", "created_at"]
    search_fields = ["employee__employee_id", "employee__first_name", "employee__last_name", "reason_code"]
    date_hierarchy = "created_at"
