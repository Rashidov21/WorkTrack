"""Attendance logs and daily summary list."""
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib import messages
from core.decorators import manager_required, admin_required
from django.utils.decorators import method_decorator

from .models import AttendanceLog, DailySummary
from .services import recompute_daily_summary


@method_decorator(manager_required, name="dispatch")
class AttendanceLogListView(LoginRequiredMixin, ListView):
    model = AttendanceLog
    template_name = "attendance/log_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("employee")
        employee_id = self.request.GET.get("employee_id")
        if employee_id:
            qs = qs.filter(employee__employee_id=employee_id)
        event = self.request.GET.get("event_type")
        if event:
            qs = qs.filter(event_type=event)
        date_str = self.request.GET.get("date")
        if date_str:
            qs = qs.filter(timestamp__date=date_str)
        return qs.order_by("-timestamp")


@method_decorator(manager_required, name="dispatch")
class DailySummaryListView(LoginRequiredMixin, ListView):
    model = DailySummary
    template_name = "attendance/summary_list.html"
    context_object_name = "summaries"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("employee")
        date_str = self.request.GET.get("date") or timezone.now().strftime("%Y-%m-%d")
        qs = qs.filter(date=date_str)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        employee_id = self.request.GET.get("employee_id")
        if employee_id:
            qs = qs.filter(employee__employee_id=employee_id)
        return qs.order_by("employee__employee_id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_date"] = self.request.GET.get("date") or timezone.now().strftime("%Y-%m-%d")
        return context


@method_decorator(admin_required, name="dispatch")
class AttendanceLogDeleteView(LoginRequiredMixin, DeleteView):
    """Admin: noto‘g‘ri davomat yozuvini o‘chirish."""
    model = AttendanceLog
    template_name = "attendance/log_confirm_delete.html"
    context_object_name = "log"
    success_url = reverse_lazy("attendance:log_list")

    def delete(self, request, *args, **kwargs):
        log = self.get_object()
        employee = log.employee
        day = log.timestamp.date()
        response = super().delete(request, *args, **kwargs)
        recompute_daily_summary(employee, day)
        messages.success(request, "Davomat yozuvi o‘chirildi.")
        return response
