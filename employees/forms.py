from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "employee_id", "first_name", "last_name", "department",
            "work_start_time", "work_end_time", "grace_period_minutes",
            "is_active", "device_person_id",
        ]
        labels = {
            "employee_id": "Xodim ID",
            "first_name": "Ism",
            "last_name": "Familiya",
            "department": "Bo‘lim",
            "work_start_time": "Ish boshlanish vaqti",
            "work_end_time": "Ish tugash vaqti",
            "grace_period_minutes": "Ruxsat etilgan muhlat (daqika)",
            "is_active": "Faol",
            "device_person_id": "Qurilma shaxs ID",
        }
        input_class = "mt-1 block w-full rounded-lg border border-slate-300 shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500 px-3 py-2 text-slate-900 placeholder-slate-400"
        checkbox_class = "rounded border-slate-300 text-slate-700 focus:ring-2 focus:ring-slate-500 h-4 w-4"
        widgets = {
            "employee_id": forms.TextInput(attrs={"class": input_class}),
            "first_name": forms.TextInput(attrs={"class": input_class}),
            "last_name": forms.TextInput(attrs={"class": input_class}),
            "department": forms.TextInput(attrs={"class": input_class}),
            "work_start_time": forms.TimeInput(attrs={"type": "time", "class": input_class}),
            "work_end_time": forms.TimeInput(attrs={"type": "time", "class": input_class}),
            "grace_period_minutes": forms.NumberInput(attrs={"class": input_class}),
            "is_active": forms.CheckboxInput(attrs={"class": checkbox_class}),
            "device_person_id": forms.TextInput(attrs={"class": input_class}),
        }
