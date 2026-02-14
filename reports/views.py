"""Reports: daily/weekly/monthly/yearly with Excel export."""
from datetime import date, timedelta
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.db.models import Sum
from django.views import View
from core.decorators import manager_required
from django.utils.decorators import method_decorator

from attendance.models import DailySummary, LatenessRecord
from penalties.models import Penalty
from .export import export_attendance_excel, export_lateness_excel, export_penalty_excel


@method_decorator(manager_required, name="dispatch")
class ReportDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_types"] = ["attendance", "lateness", "penalty"]
        return context


def get_report_date_range(request):
    period = request.GET.get("period", "day")
    end = date.today()
    if period == "day":
        start = end
    elif period == "week":
        start = end - timedelta(days=6)
    elif period == "month":
        start = end - timedelta(days=29)
    else:
        start = end.replace(month=1, day=1)
    return start, end, period


@method_decorator(manager_required, name="dispatch")
class ReportAttendanceView(LoginRequiredMixin, TemplateView):
    template_name = "reports/attendance_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start, end, period = get_report_date_range(self.request)
        context["summaries"] = DailySummary.objects.filter(date__gte=start, date__lte=end).select_related("employee").order_by("-date", "employee__employee_id")[:500]
        context["start"], context["end"] = start, end
        context["period"] = period
        return context


@method_decorator(manager_required, name="dispatch")
class ReportLatenessView(LoginRequiredMixin, TemplateView):
    template_name = "reports/lateness_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start, end, period = get_report_date_range(self.request)
        context["records"] = LatenessRecord.objects.filter(date__gte=start, date__lte=end).select_related("employee").order_by("-date", "employee__employee_id")
        context["start"], context["end"] = start, end
        context["period"] = period
        return context


@method_decorator(manager_required, name="dispatch")
class ReportPenaltyView(LoginRequiredMixin, TemplateView):
    template_name = "reports/penalty_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start, end, period = get_report_date_range(self.request)
        qs = Penalty.objects.filter(created_at__date__gte=start, created_at__date__lte=end).select_related("employee", "rule").order_by("-created_at")
        context["penalties"] = qs
        context["total"] = qs.aggregate(s=Sum("amount"))["s"] or 0
        context["start"], context["end"] = start, end
        context["period"] = period
        return context


@method_decorator(manager_required, name="dispatch")
class ExportAttendanceExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start, end, _ = get_report_date_range(request)
        buf = export_attendance_excel(start, end)
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="attendance_{start}_{end}.xlsx"'
        return response


@method_decorator(manager_required, name="dispatch")
class ExportLatenessExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start, end, _ = get_report_date_range(request)
        buf = export_lateness_excel(start, end)
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="lateness_{start}_{end}.xlsx"'
        return response


@method_decorator(manager_required, name="dispatch")
class ExportPenaltyExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start, end, _ = get_report_date_range(request)
        buf = export_penalty_excel(start, end)
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="penalties_{start}_{end}.xlsx"'
        return response
