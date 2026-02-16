from django import forms
from django.utils.translation import gettext_lazy as _
from .models import PenaltyRule, Penalty


INPUT_CLASS = "mt-1 block w-full rounded-lg border border-slate-300 shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 px-3 py-2 text-slate-900 placeholder-slate-400"
SELECT_CLASS = "mt-1 block w-full rounded-lg border border-slate-300 shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 px-3 py-2 bg-white text-slate-900"
CHECKBOX_CLASS = "rounded border-slate-300 text-slate-700 focus:ring-2 focus:ring-slate-500 h-4 w-4"
TEXTAREA_CLASS = "mt-1 block w-full rounded-lg border border-slate-300 shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 px-3 py-2 text-slate-900 placeholder-slate-400"


class PenaltyRuleForm(forms.ModelForm):
    class Meta:
        model = PenaltyRule
        fields = ["name", "rule_type", "amount_per_unit", "is_active"]
        labels = {"name": _("Nomi"), "rule_type": _("Turi"), "amount_per_unit": _("Summa / birlik"), "is_active": _("Faol")}
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "rule_type": forms.Select(attrs={"class": SELECT_CLASS}),
            "amount_per_unit": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }


class ManualPenaltyForm(forms.ModelForm):
    class Meta:
        model = Penalty
        fields = ["employee", "amount", "reason"]
        labels = {"employee": _("Xodim"), "amount": _("Summa"), "reason": _("Sabab")}
        widgets = {
            "employee": forms.Select(attrs={"class": SELECT_CLASS}),
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "reason": forms.Textarea(attrs={"rows": 2, "class": TEXTAREA_CLASS}),
        }


class PenaltyEditForm(forms.ModelForm):
    """Admin: jarima summa, sabab, qoidani tahrirlash."""
    class Meta:
        model = Penalty
        fields = ["amount", "reason", "rule"]
        labels = {"amount": _("Summa"), "reason": _("Sabab"), "rule": _("Qoida")}
        widgets = {
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "reason": forms.Textarea(attrs={"rows": 2, "class": TEXTAREA_CLASS}),
            "rule": forms.Select(attrs={"class": SELECT_CLASS}),
        }
