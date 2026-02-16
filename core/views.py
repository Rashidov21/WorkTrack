"""Core views: dashboard and settings redirect."""
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import date

from employees.models import Employee
from attendance.models import AttendanceLog, DailySummary
from penalties.models import Penalty


class DashboardView(LoginRequiredMixin, TemplateView):
    """Today overview: present, late, absent, total penalties."""
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # One query for today's summaries
        summaries_list = list(
            DailySummary.objects.filter(date=today).select_related("employee").order_by("employee__employee_id")
        )
        present_ids = [s.employee_id for s in summaries_list if s.status == DailySummary.STATUS_PRESENT]
        late_ids = [s.employee_id for s in summaries_list if s.status == DailySummary.STATUS_LATE]
        present_ids.extend(late_ids)
        absent_ids = list(
            Employee.objects.filter(is_active=True).exclude(id__in=present_ids).values_list("id", flat=True)
        )

        context["today"] = today
        context["present_count"] = len(summaries_list)
        context["late_count"] = len(late_ids)
        context["absent_count"] = len(absent_ids)
        context["total_penalties_today"] = Penalty.objects.filter(created_at__date=today).aggregate(
            s=Sum("amount")
        )["s"] or 0
        context["summaries_today"] = summaries_list[:20]
        context["chart_placeholder"] = True
        return context


class SettingsRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect to integration settings by default."""
    pattern_name = "integrations:settings"
    permanent = False


class SupportView(LoginRequiredMixin, TemplateView):
    """Yordam: qo‘llanma va bog‘lanish."""
    template_name = "core/support.html"
