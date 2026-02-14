"""Employee CRUD (admin/manager)."""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from core.decorators import admin_required, manager_required
from django.utils.decorators import method_decorator

from .models import Employee
from .forms import EmployeeForm


@method_decorator(manager_required, name="dispatch")
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.GET.get("department")
        if dept:
            qs = qs.filter(department__icontains=dept)
        active = self.request.GET.get("active")
        if active == "1":
            qs = qs.filter(is_active=True)
        elif active == "0":
            qs = qs.filter(is_active=False)
        return qs.order_by("employee_id")


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
