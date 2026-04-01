"""Penalty rules and penalty list; manual penalty (admin)."""
import json
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from core.decorators import manager_required, admin_required
from django.utils.decorators import method_decorator

from django.utils.translation import gettext as _
from core.date_range import parse_date_range, query_string_for_export
from reports.export import export_penalty_excel

from .models import Penalty, PenaltyRule, PenaltyExemption
from .forms import PenaltyRuleForm, ManualPenaltyForm, PenaltyEditForm, PenaltyExemptionForm
from notifications.tasks import send_telegram_message


@method_decorator(manager_required, name="dispatch")
class PenaltyListView(LoginRequiredMixin, ListView):
    model = Penalty
    template_name = "penalties/penalty_list.html"
    context_object_name = "penalties"
    paginate_by = 30

    def get_queryset(self):
        start, end, _ = parse_date_range(self.request, default_period="month")
        qs = super().get_queryset().select_related("employee", "rule")
        qs = qs.filter(penalty_date__gte=start, penalty_date__lte=end)
        emp = self.request.GET.get("employee_id")
        if emp:
            qs = qs.filter(employee__employee_id=emp)
        return qs.order_by("-penalty_date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start, end, mode = parse_date_range(self.request, default_period="month")
        context["filter_date_from"] = start.isoformat()
        context["filter_date_to"] = end.isoformat()
        context["period"] = "" if mode == "custom" else (self.request.GET.get("period") or "month")
        context["export_query"] = query_string_for_export(
            self.request,
            allowed_keys={"date_from", "date_to", "period", "employee_id"},
        )
        return context


@method_decorator(manager_required, name="dispatch")
class PenaltyExportExcelView(LoginRequiredMixin, View):
    """Filtrlangan jarimalarni Excelga (hisobot bilan bir xil stunlar)."""

    def get(self, request, *args, **kwargs):
        start, end, _ = parse_date_range(request, default_period="month")
        emp = (request.GET.get("employee_id") or "").strip() or None
        buf = export_penalty_excel(start, end, employee_id=emp)
        response = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="penalties_list_{start}_{end}.xlsx"'
        return response


@method_decorator(admin_required, name="dispatch")
class PenaltyRuleListView(LoginRequiredMixin, ListView):
    model = PenaltyRule
    template_name = "penalties/rule_list.html"
    context_object_name = "rules"


@method_decorator(admin_required, name="dispatch")
class PenaltyRuleCreateView(LoginRequiredMixin, CreateView):
    model = PenaltyRule
    form_class = PenaltyRuleForm
    template_name = "penalties/rule_form.html"
    success_url = reverse_lazy("penalties:rule_list")


@method_decorator(admin_required, name="dispatch")
class PenaltyRuleUpdateView(LoginRequiredMixin, UpdateView):
    model = PenaltyRule
    form_class = PenaltyRuleForm
    template_name = "penalties/rule_form.html"
    context_object_name = "rule"
    success_url = reverse_lazy("penalties:rule_list")


@method_decorator(admin_required, name="dispatch")
class ManualPenaltyCreateView(LoginRequiredMixin, CreateView):
    form_class = ManualPenaltyForm
    template_name = "penalties/penalty_manual.html"
    success_url = reverse_lazy("penalties:list")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        rule_types = {
            str(r.id): r.rule_type for r in PenaltyRule.objects.filter(is_active=True)
        }
        data["rule_types_by_id_json"] = json.dumps(rule_types)
        return data

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.is_manual = True
        messages.success(self.request, "Jarima qo'shildi.")
        response = super().form_valid(form)
        p = form.instance
        date_str = getattr(p, "penalty_date", None)
        date_part = f" Sana: {date_str}." if date_str else ""
        if p.penalty_percent is not None:
            msg = f"Penalty (manual): {p.employee.get_full_name()} ({p.employee.employee_id}) — {p.penalty_percent}%.{date_part} Sabab: {p.reason or 'N/A'}"
        else:
            msg = f"Penalty (manual): {p.employee.get_full_name()} ({p.employee.employee_id}) — {p.amount} so'm.{date_part} Sabab: {p.reason or 'N/A'}"
        send_telegram_message.delay(msg)
        return response


@method_decorator(admin_required, name="dispatch")
class PenaltyHistoryView(LoginRequiredMixin, ListView):
    model = Penalty
    template_name = "penalties/penalty_list.html"
    context_object_name = "penalties"
    paginate_by = 30

    def get_queryset(self):
        return Penalty.objects.filter(employee_id=self.kwargs["pk"]).select_related("rule").order_by("-penalty_date", "-created_at")


@method_decorator(admin_required, name="dispatch")
class PenaltyUpdateView(LoginRequiredMixin, UpdateView):
    """Admin: jarima summa/sabab/qoidani tahrirlash."""
    model = Penalty
    form_class = PenaltyEditForm
    template_name = "penalties/penalty_edit.html"
    context_object_name = "penalty"
    success_url = reverse_lazy("penalties:list")

    def form_valid(self, form):
        messages.success(self.request, "Jarima saqlandi.")
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class PenaltyDeleteView(LoginRequiredMixin, DeleteView):
    """Admin: jarimani o'chirish."""
    model = Penalty
    template_name = "penalties/penalty_confirm_delete.html"
    context_object_name = "penalty"
    success_url = reverse_lazy("penalties:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Jarima o'chirildi.")
        return response


@method_decorator(admin_required, name="dispatch")
class PenaltyRuleDeleteView(LoginRequiredMixin, DeleteView):
    """Admin: jarima qoidasini o'chirish."""
    model = PenaltyRule
    template_name = "penalties/rule_confirm_delete.html"
    context_object_name = "rule"
    success_url = reverse_lazy("penalties:rule_list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Jarima qoidasi o'chirildi.")
        return response


# ——— Jarimadan ozod ———
@method_decorator(manager_required, name="dispatch")
class PenaltyExemptionListView(LoginRequiredMixin, ListView):
    model = PenaltyExemption
    template_name = "penalties/exemption_list.html"
    context_object_name = "exemptions"
    paginate_by = 30

    def get_queryset(self):
        qs = PenaltyExemption.objects.select_related("employee", "created_by").order_by("-date_from")
        emp = self.request.GET.get("employee_id")
        if emp:
            qs = qs.filter(employee__employee_id=emp)
        return qs


@method_decorator(admin_required, name="dispatch")
class PenaltyExemptionCreateView(LoginRequiredMixin, CreateView):
    model = PenaltyExemption
    form_class = PenaltyExemptionForm
    template_name = "penalties/exemption_form.html"
    success_url = reverse_lazy("penalties:exemption_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _("Jarimadan ozod qo'shildi."))
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class PenaltyExemptionUpdateView(LoginRequiredMixin, UpdateView):
    model = PenaltyExemption
    form_class = PenaltyExemptionForm
    template_name = "penalties/exemption_form.html"
    context_object_name = "exemption"
    success_url = reverse_lazy("penalties:exemption_list")

    def form_valid(self, form):
        messages.success(self.request, _("Jarimadan ozod saqlandi."))
        return super().form_valid(form)


@method_decorator(admin_required, name="dispatch")
class PenaltyExemptionDeleteView(LoginRequiredMixin, DeleteView):
    model = PenaltyExemption
    template_name = "penalties/exemption_confirm_delete.html"
    context_object_name = "exemption"
    success_url = reverse_lazy("penalties:exemption_list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("Jarimadan ozod o'chirildi."))
        return response
