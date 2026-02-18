"""Penalty rules and penalty list; manual penalty (admin)."""
import json
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from core.decorators import manager_required, admin_required
from django.utils.decorators import method_decorator

from .models import Penalty, PenaltyRule
from .forms import PenaltyRuleForm, ManualPenaltyForm, PenaltyEditForm
from notifications.tasks import send_telegram_message


@method_decorator(manager_required, name="dispatch")
class PenaltyListView(LoginRequiredMixin, ListView):
    model = Penalty
    template_name = "penalties/penalty_list.html"
    context_object_name = "penalties"
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related("employee", "rule")
        emp = self.request.GET.get("employee_id")
        if emp:
            qs = qs.filter(employee__employee_id=emp)
        return qs.order_by("-created_at")


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
        messages.success(self.request, "Jarima qo‘shildi.")
        response = super().form_valid(form)
        p = form.instance
        if p.penalty_percent is not None:
            msg = f"Penalty (manual): {p.employee.get_full_name()} ({p.employee.employee_id}) — {p.penalty_percent}%. Reason: {p.reason or 'N/A'}"
        else:
            msg = f"Penalty (manual): {p.employee.get_full_name()} ({p.employee.employee_id}) — {p.amount}. Reason: {p.reason or 'N/A'}"
        send_telegram_message.delay(msg)
        return response


@method_decorator(admin_required, name="dispatch")
class PenaltyHistoryView(LoginRequiredMixin, ListView):
    model = Penalty
    template_name = "penalties/penalty_list.html"
    context_object_name = "penalties"
    paginate_by = 30

    def get_queryset(self):
        return Penalty.objects.filter(employee_id=self.kwargs["pk"]).select_related("rule").order_by("-created_at")


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
    """Admin: jarimani o‘chirish."""
    model = Penalty
    template_name = "penalties/penalty_confirm_delete.html"
    context_object_name = "penalty"
    success_url = reverse_lazy("penalties:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Jarima o‘chirildi.")
        return response


@method_decorator(admin_required, name="dispatch")
class PenaltyRuleDeleteView(LoginRequiredMixin, DeleteView):
    """Admin: jarima qoidasini o‘chirish."""
    model = PenaltyRule
    template_name = "penalties/rule_confirm_delete.html"
    context_object_name = "rule"
    success_url = reverse_lazy("penalties:rule_list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Jarima qoidasi o‘chirildi.")
        return response
