"""Penalty rules and penalty list; manual penalty (admin)."""
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from core.decorators import manager_required, admin_required
from django.utils.decorators import method_decorator

from .models import Penalty, PenaltyRule
from .forms import PenaltyRuleForm, ManualPenaltyForm
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

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.is_manual = True
        messages.success(self.request, "Jarima qo‘shildi.")
        response = super().form_valid(form)
        # Notify via Telegram
        send_telegram_message.delay(
            f"Penalty (manual): {form.instance.employee.get_full_name()} ({form.instance.employee.employee_id}) — {form.instance.amount}. Reason: {form.instance.reason or 'N/A'}"
        )
        return response


@method_decorator(admin_required, name="dispatch")
class PenaltyHistoryView(LoginRequiredMixin, ListView):
    model = Penalty
    template_name = "penalties/penalty_list.html"
    context_object_name = "penalties"
    paginate_by = 30

    def get_queryset(self):
        return Penalty.objects.filter(employee_id=self.kwargs["pk"]).select_related("rule").order_by("-created_at")
