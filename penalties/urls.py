from django.urls import path
from . import views

app_name = "penalties"

urlpatterns = [
    path("", views.PenaltyListView.as_view(), name="list"),
    path("add-manual/", views.ManualPenaltyCreateView.as_view(), name="add_manual"),
    path("<int:pk>/edit/", views.PenaltyUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.PenaltyDeleteView.as_view(), name="delete"),
    path("rules/", views.PenaltyRuleListView.as_view(), name="rule_list"),
    path("rules/add/", views.PenaltyRuleCreateView.as_view(), name="rule_add"),
    path("rules/<int:pk>/edit/", views.PenaltyRuleUpdateView.as_view(), name="rule_edit"),
    path("rules/<int:pk>/delete/", views.PenaltyRuleDeleteView.as_view(), name="rule_delete"),
    path("employee/<int:pk>/", views.PenaltyHistoryView.as_view(), name="employee_history"),
    path("exemptions/", views.PenaltyExemptionListView.as_view(), name="exemption_list"),
    path("exemptions/add/", views.PenaltyExemptionCreateView.as_view(), name="exemption_add"),
    path("exemptions/<int:pk>/edit/", views.PenaltyExemptionUpdateView.as_view(), name="exemption_edit"),
    path("exemptions/<int:pk>/delete/", views.PenaltyExemptionDeleteView.as_view(), name="exemption_delete"),
]
