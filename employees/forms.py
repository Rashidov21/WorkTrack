from django import forms
from .models import Employee, WorkSchedule

# 0=Dushanba, 1=Seshanba, ... 6=Yakshanba (Python weekday)
WEEKDAY_CHOICES = [
    (0, "Dushanba"),
    (1, "Seshanba"),
    (2, "Chorshanba"),
    (3, "Payshanba"),
    (4, "Juma"),
    (5, "Shanba"),
    (6, "Yakshanba"),
]


class WorkScheduleForm(forms.ModelForm):
    """Ish grafigi formasi — ish kunlari checkboxlar orqali."""
    working_days_choice = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Ish kunlari",
        help_text="Ish ishlanadigan hafta kunlarini tanlang.",
    )

    class Meta:
        model = WorkSchedule
        fields = ["name", "work_start_time", "work_end_time", "grace_period_minutes", "is_active"]
        labels = {
            "name": "Grafik nomi",
            "work_start_time": "Ish boshlanish vaqti",
            "work_end_time": "Ish tugash vaqti",
            "grace_period_minutes": "Ruxsat etilgan muhlat (daqika)",
            "is_active": "Faol",
        }
        help_texts = {
            "grace_period_minutes": "Ish boshlanish vaqtidan keyin shuncha daqiqa kechikishga ruxsat.",
        }
        input_class = "mt-1 block w-full rounded-lg border border-slate-300 shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 px-3 py-2 text-slate-900 placeholder-slate-400"
        checkbox_class = "rounded border-slate-300 text-slate-700 focus:ring-2 focus:ring-slate-500 h-4 w-4"
        widgets = {
            "name": forms.TextInput(attrs={"class": input_class}),
            "work_start_time": forms.TimeInput(attrs={"type": "time", "class": input_class}),
            "work_end_time": forms.TimeInput(attrs={"type": "time", "class": input_class}),
            "grace_period_minutes": forms.NumberInput(attrs={"class": input_class}),
            "is_active": forms.CheckboxInput(attrs={"class": checkbox_class}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.working_days:
            try:
                self.fields["working_days_choice"].initial = [
                    int(x.strip()) for x in self.instance.working_days.split(",") if x.strip().isdigit()
                ]
            except (ValueError, AttributeError):
                self.fields["working_days_choice"].initial = [0, 1, 2, 3, 4]
        else:
            # Yangi grafik: standart dushanba–juma
            self.fields["working_days_choice"].initial = [0, 1, 2, 3, 4]

    def save(self, commit=True):
        instance = super().save(commit=False)
        choice = self.cleaned_data.get("working_days_choice") or []
        instance.working_days = ",".join(str(x) for x in sorted(int(c) for c in choice)) if choice else "0,1,2,3,4"
        if commit:
            instance.save()
        return instance


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "employee_id", "first_name", "last_name", "department",
            "work_schedule",
            "work_start_time", "work_end_time", "grace_period_minutes",
            "is_active", "device_person_id", "telegram_username",
        ]
        labels = {
            "employee_id": "Xodim ID",
            "first_name": "Ism",
            "last_name": "Familiya",
            "department": "Bo‘lim",
            "work_schedule": "Ish grafigi",
            "work_start_time": "Ish boshlanish vaqti (grafik tanlanmasa)",
            "work_end_time": "Ish tugash vaqti (grafik tanlanmasa)",
            "grace_period_minutes": "Ruxsat etilgan muhlat (grafik tanlanmasa)",
            "is_active": "Faol",
            "device_person_id": "Qurilma shaxs ID",
            "telegram_username": "Telegram username (ixtiyoriy)",
        }
        input_class = "mt-1 block w-full rounded-lg border border-slate-300 shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 px-3 py-2 text-slate-900 placeholder-slate-400"
        checkbox_class = "rounded border-slate-300 text-slate-700 focus:ring-2 focus:ring-slate-500 h-4 w-4"
        select_class = "mt-1 block w-full rounded-lg border border-slate-300 shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 px-3 py-2 bg-white text-slate-900"
        widgets = {
            "employee_id": forms.TextInput(attrs={"class": input_class}),
            "first_name": forms.TextInput(attrs={"class": input_class}),
            "last_name": forms.TextInput(attrs={"class": input_class}),
            "department": forms.TextInput(attrs={"class": input_class}),
            "work_schedule": forms.Select(attrs={"class": select_class}),
            "work_start_time": forms.TimeInput(attrs={"type": "time", "class": input_class}),
            "work_end_time": forms.TimeInput(attrs={"type": "time", "class": input_class}),
            "grace_period_minutes": forms.NumberInput(attrs={"class": input_class}),
            "is_active": forms.CheckboxInput(attrs={"class": checkbox_class}),
            "device_person_id": forms.TextInput(attrs={"class": input_class}),
            "telegram_username": forms.TextInput(attrs={"class": input_class, "placeholder": "username (@ siz)"}),
        }
