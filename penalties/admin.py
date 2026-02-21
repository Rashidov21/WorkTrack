from django.contrib import admin
from .models import PenaltyRule, Penalty, PenaltyExemption


@admin.register(PenaltyRule)
class PenaltyRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "rule_type", "amount_per_unit", "is_active"]


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
