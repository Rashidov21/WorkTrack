from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import PenaltyRule, Penalty, PenaltyExemption


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
        if "penalty_date" in self.fields and not self.instance.pk:
            self.fields["penalty_date"].initial = timezone.now().date()

    class Meta:
        model = Penalty
        fields = ["employee", "rule", "amount", "penalty_percent", "penalty_date", "reason"]
        labels = {
            "employee": _("Xodim"),
            "rule": _("Qoida (turi)"),
            "amount": _("Summa (so'm)"),
            "penalty_percent": _("Jarima foizi (%)"),
            "penalty_date": _("Jarima sanasi (qaysi kun uchun)"),
            "reason": _("Sabab"),
        }
        help_texts = {
            "rule": _("Qaysi jarima qoidasiga bog'lash. Oylikdan foiz tanlasangiz, foiz (%) ni kiriting."),
            "penalty_percent": _("Faqat «Oylikdan foiz» qoidasi uchun (masalan 1 yoki 2)."),
            "penalty_date": _("Jarima qaysi kun (davomat sanasi) uchun ekanini belgilang."),
        }
        widgets = {
            "employee": forms.Select(attrs={"class": SELECT_CLASS}),
            "rule": forms.Select(attrs={"class": SELECT_CLASS}),
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "0"}),
            "penalty_percent": forms.NumberInput(attrs={"class": INPUT_CLASS, "placeholder": "1 yoki 2", "step": "0.01"}),
            "penalty_date": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}),
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
    """Admin: jarima summa, sabab, sana, qoidani tahrirlash."""
    class Meta:
        model = Penalty
        fields = ["amount", "reason", "penalty_date", "rule"]
        labels = {"amount": _("Summa"), "reason": _("Sabab"), "penalty_date": _("Jarima sanasi"), "rule": _("Qoida")}
        widgets = {
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASS}),
            "reason": forms.Textarea(attrs={"rows": 2, "class": TEXTAREA_CLASS}),
            "penalty_date": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}),
            "rule": forms.Select(attrs={"class": SELECT_CLASS}),
        }


class PenaltyExemptionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and "date_to" in self.fields:
            today = timezone.now().date()
            self.fields["date_from"].initial = today
            self.fields["date_to"].initial = today

    def clean(self):
        data = super().clean()
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        if date_from and date_to and date_to < date_from:
            self.add_error("date_to", _("Gacha sanasi Dan sanasidan keyin bo'lishi kerak."))
        return data

    class Meta:
        model = PenaltyExemption
        fields = ["employee", "date_from", "date_to", "reason_type", "reason_text"]
        labels = {
            "employee": _("Xodim"),
            "date_from": _("Dan (sana)"),
            "date_to": _("Gacha (sana)"),
            "reason_type": _("Sabab"),
            "reason_text": _("Izoh (ixtiyoriy)"),
        }
        help_texts = {
            "date_from": _("Jarima yozilmasin, shu kundan boshlab."),
            "date_to": _("Shu kungacha. Bir kun uchun Dan = Gacha qiling."),
        }
        widgets = {
            "employee": forms.Select(attrs={"class": SELECT_CLASS}),
            "date_from": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}),
            "date_to": forms.DateInput(attrs={"class": INPUT_CLASS, "type": "date"}),
            "reason_type": forms.Select(attrs={"class": SELECT_CLASS}),
            "reason_text": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": _("Qisqa izoh")}),
        }
