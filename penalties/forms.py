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
        fields = [
            "name", "rule_type",
            "threshold_minutes", "percent_if_late_le_threshold", "percent_if_late_gt_threshold",
            "amount_per_unit", "max_amount_per_day",
            "is_active",
        ]
        labels = {
            "name": _("Nomi"),
            "rule_type": _("Turi"),
            "threshold_minutes": _("Chegara (daq)"),
            "percent_if_late_le_threshold": _("Foiz (≤ chegara)"),
            "percent_if_late_gt_threshold": _("Foiz (> chegara)"),
            "amount_per_unit": _("Summa / birlik"),
            "max_amount_per_day": _("Kunlik maksimum (so'm)"),
            "is_active": _("Faol"),
        }
        help_texts = {
            "threshold_minutes": _("Oylikdan foiz: shu daqiqagacha birinchi foiz, undan keyin ikkinchi foiz (masalan 30)."),
            "percent_if_late_le_threshold": _("Kechikish chegara daqiqagacha bo'lsa (masalan 1 = 1%)."),
            "percent_if_late_gt_threshold": _("Kechikish chegaradan oshsa (masalan 2 = 2%)."),
            "max_amount_per_day": _("Bir xodim uchun shu kundagi jami jarima shu summandan oshmasin. Faqat har daqiqaga/qat'iy summa uchun."),
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "rule_type": forms.Select(attrs={"class": SELECT_CLASS}),
            "threshold_minutes": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "30"}),
            "percent_if_late_le_threshold": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "1", "step": "0.01"}),
            "percent_if_late_gt_threshold": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "2", "step": "0.01"}),
            "amount_per_unit": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "max_amount_per_day": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "50000"}),
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
