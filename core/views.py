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

        # Summaries for today
        summaries_today = DailySummary.objects.filter(date=today).select_related("employee")
        present_ids = list(summaries_today.filter(status=DailySummary.STATUS_PRESENT).values_list("employee_id", flat=True))
        late_ids = list(summaries_today.filter(status=DailySummary.STATUS_LATE).values_list("employee_id", flat=True))
        absent_ids = list(
            Employee.objects.filter(is_active=True).exclude(id__in=present_ids + late_ids).values_list("id", flat=True)
        )

        context["today"] = today
        context["present_count"] = len(present_ids) + len(late_ids)  # present includes on-time + late
        context["late_count"] = len(late_ids)
        context["absent_count"] = len(absent_ids)
        context["total_penalties_today"] = Penalty.objects.filter(created_at__date=today).aggregate(
            s=Sum("amount")
        )["s"] or 0
        context["summaries_today"] = summaries_today[:20]
        context["chart_placeholder"] = True
        return context


class SettingsRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect to integration settings by default."""
    pattern_name = "integrations:settings"
    permanent = False
