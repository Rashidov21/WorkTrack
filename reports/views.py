"""Reports: daily/weekly/monthly/yearly with Excel export."""
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.db.models import Sum
from django.views import View
from core.decorators import manager_required
from django.utils.decorators import method_decorator

from attendance.models import DailySummary, LatenessRecord
from penalties.models import Penalty
from core.date_range import parse_date_range, query_string_for_export
from .export import export_attendance_excel, export_lateness_excel, export_penalty_excel

REPORT_ROW_LIMIT = 500


@method_decorator(manager_required, name="dispatch")
class ReportDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_types"] = ["attendance", "lateness", "penalty"]
        return context


def _report_context(request):
    start, end, mode = parse_date_range(request, default_period="month")
    export_q = query_string_for_export(
        request,
        allowed_keys={"date_from", "date_to", "period"},
    )
    if mode == "custom":
        period_val = ""
    else:
        period_val = request.GET.get("period") or "month"
    return {
        "start": start,
        "end": end,
        "date_mode": mode,
        "filter_date_from": start.isoformat(),
        "filter_date_to": end.isoformat(),
        "period": period_val,
        "export_query": export_q,
    }


@method_decorator(manager_required, name="dispatch")
class ReportAttendanceView(LoginRequiredMixin, TemplateView):
    template_name = "reports/attendance_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ctx = _report_context(self.request)
        start, end = ctx["start"], ctx["end"]
        base = DailySummary.objects.filter(date__gte=start, date__lte=end).select_related("employee")
        total = base.count()
        context.update(ctx)
        context["summaries"] = base.order_by("-date", "employee__employee_id")[:REPORT_ROW_LIMIT]
        context["report_truncated"] = total > REPORT_ROW_LIMIT
        context["report_row_limit"] = REPORT_ROW_LIMIT
        return context


@method_decorator(manager_required, name="dispatch")
class ReportLatenessView(LoginRequiredMixin, TemplateView):
    template_name = "reports/lateness_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ctx = _report_context(self.request)
        start, end = ctx["start"], ctx["end"]
        base = LatenessRecord.objects.filter(date__gte=start, date__lte=end).select_related("employee")
        total = base.count()
        context.update(ctx)
        context["records"] = base.order_by("-date", "employee__employee_id")[:REPORT_ROW_LIMIT]
        context["report_truncated"] = total > REPORT_ROW_LIMIT
        context["report_row_limit"] = REPORT_ROW_LIMIT
        return context


@method_decorator(manager_required, name="dispatch")
class ReportPenaltyView(LoginRequiredMixin, TemplateView):
    template_name = "reports/penalty_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ctx = _report_context(self.request)
        start, end = ctx["start"], ctx["end"]
        base = Penalty.objects.filter(penalty_date__gte=start, penalty_date__lte=end).select_related("employee", "rule")
        total = base.count()
        context.update(ctx)
        context["penalties"] = base.order_by("-penalty_date", "-created_at")[:REPORT_ROW_LIMIT]
        context["report_truncated"] = total > REPORT_ROW_LIMIT
        context["report_row_limit"] = REPORT_ROW_LIMIT
        context["total"] = base.aggregate(s=Sum("amount"))["s"] or 0
        return context


@method_decorator(manager_required, name="dispatch")
class ExportAttendanceExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start, end, _ = parse_date_range(request, default_period="month")
        buf = export_attendance_excel(start, end)
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="attendance_{start}_{end}.xlsx"'
        return response


@method_decorator(manager_required, name="dispatch")
class ExportLatenessExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start, end, _ = parse_date_range(request, default_period="month")
        buf = export_lateness_excel(start, end)
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="lateness_{start}_{end}.xlsx"'
        return response


@method_decorator(manager_required, name="dispatch")
class ExportPenaltyExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        start, end, _ = parse_date_range(request, default_period="month")
        buf = export_penalty_excel(start, end)
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="penalties_{start}_{end}.xlsx"'
        return response
