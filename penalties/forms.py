from django import forms
from .models import PenaltyRule, Penalty


class PenaltyRuleForm(forms.ModelForm):
    class Meta:
        model = PenaltyRule
        fields = ["name", "rule_type", "amount_per_unit", "is_active"]


class ManualPenaltyForm(forms.ModelForm):
    class Meta:
        model = Penalty
        fields = ["employee", "amount", "reason"]
        widgets = {"reason": forms.Textarea(attrs={"rows": 2})}
