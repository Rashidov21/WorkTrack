from django import forms
from .models import PenaltyRule, Penalty


class PenaltyRuleForm(forms.ModelForm):
    class Meta:
        model = PenaltyRule
        fields = ["name", "rule_type", "amount_per_unit", "is_active"]
        labels = {"name": "Nomi", "rule_type": "Turi", "amount_per_unit": "Summa / birlik", "is_active": "Faol"}


class ManualPenaltyForm(forms.ModelForm):
    class Meta:
        model = Penalty
        fields = ["employee", "amount", "reason"]
        labels = {"employee": "Xodim", "amount": "Summa", "reason": "Sabab"}
        widgets = {"reason": forms.Textarea(attrs={"rows": 2})}
