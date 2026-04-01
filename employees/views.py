"""Employee CRUD (admin/manager) and WorkSchedule CRUD."""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.decorators import admin_required, manager_required
from django.utils.decorators import method_decorator

from penalties.models import PenaltyExemption

from .models import Employee, WorkSchedule
from .forms import EmployeeForm, WorkScheduleForm


@method_decorator(manager_required, name="dispatch")
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        dept_pick = (self.request.GET.get("department") or "").strip()
        if dept_pick:
            qs = qs.filter(department=dept_pick)
        active = self.request.GET.get("active")
        if active == "1":
            qs = qs.filter(is_active=True)
        elif active == "0":
            qs = qs.filter(is_active=False)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(employee_id__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(device_person_id__icontains=q)
            )
        sched = self.request.GET.get("schedule")
        if sched:
            qs = qs.filter(work_schedule_id=sched)
        return qs.order_by("employee_id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["department_list"] = (
            Employee.objects.exclude(department__exact="")
            .values_list("department", flat=True)
            .distinct()
            .order_by("department")
        )
        context["schedule_choices"] = [
            (str(s.pk), s.name) for s in WorkSchedule.objects.filter(is_active=True).order_by("name")
        ]
        return context


@method_decorator(manager_required, name="dispatch")
class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = "employees/employee_detail.html"
    context_object_name = "employee"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emp = self.object
        context["attendance_logs"] = emp.attendance_logs.all()[:50]
        context["daily_summaries"] = emp.daily_summaries.all().order_by("-date")[:30]
        context["lateness_records"] = emp.lateness_records.all().order_by("-date")[:30]
        context["penalties"] = emp.penalties.all()[:30]
        context["penalty_exemptions"] = (
            PenaltyExemption.objects.filter(employee=emp).order_by("-date_from")[:20]
        )
        return context


@method_decorator(admin_required, name="dispatch")
class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employees:list")


@method_decorator(admin_required, name="dispatch")
class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    context_object_name = "employee"
    success_url = reverse_lazy("employees:list")


@method_decorator(admin_required, name="dispatch")
class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = "employees/employee_confirm_delete.html"
    success_url = reverse_lazy("employees:list")
    context_object_name = "employee"


# ——— Ish grafiklari (WorkSchedule) ——— admin only
@method_decorator(admin_required, name="dispatch")
class ScheduleListView(LoginRequiredMixin, ListView):
    model = WorkSchedule
    template_name = "employees/schedule_list.html"
    context_object_name = "schedules"
    ordering = ["name"]


@method_decorator(admin_required, name="dispatch")
class ScheduleCreateView(LoginRequiredMixin, CreateView):
    model = WorkSchedule
    form_class = WorkScheduleForm
    template_name = "employees/schedule_form.html"
    success_url = reverse_lazy("employees:schedule_list")


@method_decorator(admin_required, name="dispatch")
class ScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkSchedule
    form_class = WorkScheduleForm
    template_name = "employees/schedule_form.html"
    context_object_name = "schedule"
    success_url = reverse_lazy("employees:schedule_list")


@method_decorator(admin_required, name="dispatch")
class ScheduleDeleteView(LoginRequiredMixin, DeleteView):
    model = WorkSchedule
    template_name = "employees/schedule_confirm_delete.html"
    success_url = reverse_lazy("employees:schedule_list")
    context_object_name = "schedule"
