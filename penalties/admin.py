from django.contrib import admin
from .models import PenaltyRule, Penalty


@admin.register(PenaltyRule)
class PenaltyRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "rule_type", "amount_per_unit", "is_active"]


@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ["employee", "amount", "rule", "is_manual", "created_at"]
    list_filter = ["is_manual"]
    date_hierarchy = "created_at"
