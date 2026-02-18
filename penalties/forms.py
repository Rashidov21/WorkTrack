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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rule"].queryset = PenaltyRule.objects.filter(is_active=True).order_by("name")
        self.fields["rule"].required = False
        self.fields["rule"].empty_label = _("— Qoida tanlanmagan —")
        self.fields["amount"].required = False
        self.fields["penalty_percent"].required = False

    class Meta:
        model = Penalty
        fields = ["employee", "rule", "amount", "penalty_percent", "reason"]
        labels = {
            "employee": _("Xodim"),
            "rule": _("Qoida (turi)"),
            "amount": _("Summa (so'm)"),
            "penalty_percent": _("Jarima foizi (%)"),
            "reason": _("Sabab"),
        }
        help_texts = {
            "rule": _("Qaysi jarima qoidasiga bog'lash. Oylikdan foiz tanlasangiz, foiz (%) ni kiriting."),
            "penalty_percent": _("Faqat «Oylikdan foiz» qoidasi uchun (masalan 1 yoki 2)."),
        }
        widgets = {
            "employee": forms.Select(attrs={"class": SELECT_CLASS}),
            "rule": forms.Select(attrs={"class": SELECT_CLASS}),
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "0"}),
            "penalty_percent": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "1 yoki 2", "step": "0.01"}),
            "reason": forms.Textarea(attrs={"rows": 2, "class": TEXTAREA_CLASS}),
        }

    def clean(self):
        data = super().clean()
        rule = data.get("rule")
        amount = data.get("amount")
        penalty_percent = data.get("penalty_percent")
        if rule and rule.rule_type == "percent_of_salary":
            if penalty_percent is None:
                self.add_error("penalty_percent", _("Oylikdan foiz qoidasi uchun foiz (%) kiriting."))
            data["amount"] = 0
        else:
            if amount is None or amount < 0:
                self.add_error("amount", _("Summa kiriting."))
            if penalty_percent is not None:
                data["penalty_percent"] = None
        return data


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
