"""Attendance logs and daily summary list."""
from django.views.generic import ListView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from core.decorators import manager_required, admin_required
from django.utils.decorators import method_decorator

from core.date_range import parse_date_range, query_string_for_export
from reports.export import export_attendance_logs_excel

from .models import AttendanceLog, DailySummary
from .services import recompute_daily_summary


@method_decorator(manager_required, name="dispatch")
class AttendanceLogListView(LoginRequiredMixin, ListView):
    model = AttendanceLog
    template_name = "attendance/log_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        start, end, _ = parse_date_range(self.request, default_period="month")
        qs = super().get_queryset().select_related("employee")
        qs = qs.filter(timestamp__date__gte=start, timestamp__date__lte=end)
        employee_id = self.request.GET.get("employee_id")
        if employee_id:
            qs = qs.filter(employee__employee_id=employee_id)
        event = self.request.GET.get("event_type")
        if event:
            qs = qs.filter(event_type=event)
        return qs.order_by("-timestamp")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start, end, mode = parse_date_range(self.request, default_period="month")
        context["filter_date_from"] = start.isoformat()
        context["filter_date_to"] = end.isoformat()
        context["period"] = "" if mode == "custom" else (self.request.GET.get("period") or "month")
        context["export_query"] = query_string_for_export(
            self.request,
            allowed_keys={"date_from", "date_to", "period", "employee_id", "event_type"},
        )
        return context


@method_decorator(manager_required, name="dispatch")
class AttendanceLogsExportExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start, end, _ = parse_date_range(request, default_period="month")
        emp = (request.GET.get("employee_id") or "").strip() or None
        ev = (request.GET.get("event_type") or "").strip() or None
        buf = export_attendance_logs_excel(start, end, employee_id=emp, event_type=ev)
        response = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="attendance_logs_{start}_{end}.xlsx"'
        return response


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
