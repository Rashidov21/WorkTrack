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
        widgets = {
            "employee_id": forms.TextInput(attrs={"class": "mt-1 block w-full rounded-lg border-slate-300 shadow-sm"}),
            "first_name": forms.TextInput(attrs={"class": "mt-1 block w-full rounded-lg border-slate-300 shadow-sm"}),
            "last_name": forms.TextInput(attrs={"class": "mt-1 block w-full rounded-lg border-slate-300 shadow-sm"}),
            "department": forms.TextInput(attrs={"class": "mt-1 block w-full rounded-lg border-slate-300 shadow-sm"}),
            "work_start_time": forms.TimeInput(attrs={"type": "time", "class": "mt-1 block w-full rounded-lg border-slate-300"}),
            "work_end_time": forms.TimeInput(attrs={"type": "time", "class": "mt-1 block w-full rounded-lg border-slate-300"}),
            "grace_period_minutes": forms.NumberInput(attrs={"class": "mt-1 block w-full rounded-lg border-slate-300"}),
            "device_person_id": forms.TextInput(attrs={"class": "mt-1 block w-full rounded-lg border-slate-300 shadow-sm"}),
        }
