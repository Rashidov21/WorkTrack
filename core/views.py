"""Core views: dashboard and settings redirect."""
import json
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.translation import gettext
from datetime import date, timedelta

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

        # Chart: oxirgi 30 kun (1 oy) — har kuni kelganlar soni (present + late)
        month_ago = today - timedelta(days=29)
        chart_labels = []
        chart_data = []
        for i in range(30):
            d = month_ago + timedelta(days=i)
            chart_labels.append(d.strftime("%d.%m"))
            cnt = DailySummary.objects.filter(
                date=d,
                status__in=[DailySummary.STATUS_PRESENT, DailySummary.STATUS_LATE],
            ).count()
            chart_data.append(cnt)
        context["chart_labels_json"] = json.dumps(chart_labels)
        context["chart_data_json"] = json.dumps(chart_data)
        context["chart_dataset_label"] = gettext("Kelganlar")

        # Kechikkanlar (bugun)
        context["late_today"] = [s for s in summaries_list if s.status == DailySummary.STATUS_LATE]

        # Haftalik (oxirgi 7 kun)
        week_ago = today - timedelta(days=6)
        context["week_came_count"] = DailySummary.objects.filter(
            date__gte=week_ago, date__lte=today,
            status__in=[DailySummary.STATUS_PRESENT, DailySummary.STATUS_LATE],
        ).count()
        context["week_late_count"] = DailySummary.objects.filter(
            date__gte=week_ago, date__lte=today, status=DailySummary.STATUS_LATE,
        ).count()
        w_pen = Penalty.objects.filter(
            created_at__date__gte=week_ago, created_at__date__lte=today,
        ).aggregate(s=Sum("amount"))
        context["week_penalties_sum"] = int(w_pen["s"] or 0)

        # Oylik (joriy oy)
        month_start = today.replace(day=1)
        context["month_came_count"] = DailySummary.objects.filter(
            date__gte=month_start, date__lte=today,
            status__in=[DailySummary.STATUS_PRESENT, DailySummary.STATUS_LATE],
        ).count()
        context["month_late_count"] = DailySummary.objects.filter(
            date__gte=month_start, date__lte=today, status=DailySummary.STATUS_LATE,
        ).count()
        m_pen = Penalty.objects.filter(
            created_at__date__gte=month_start, created_at__date__lte=today,
        ).aggregate(s=Sum("amount"), c=Count("id"))
        context["month_penalties_sum"] = int(m_pen["s"] or 0)
        context["month_penalties_count"] = m_pen["c"] or 0

        # Xodimlar
        context["employees_active_count"] = Employee.objects.filter(is_active=True).count()
        context["employees_total_count"] = Employee.objects.count()

        return context


class SettingsRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect to integration settings by default."""
    pattern_name = "integrations:settings"
    permanent = False


class SupportView(LoginRequiredMixin, TemplateView):
    """Yordam: qo‘llanma va bog‘lanish."""
    template_name = "core/support.html"
