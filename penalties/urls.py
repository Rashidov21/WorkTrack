from django.urls import path
from . import views

app_name = "penalties"

urlpatterns = [
    path("", views.PenaltyListView.as_view(), name="list"),
    path("add-manual/", views.ManualPenaltyCreateView.as_view(), name="add_manual"),
    path("rules/", views.PenaltyRuleListView.as_view(), name="rule_list"),
    path("rules/add/", views.PenaltyRuleCreateView.as_view(), name="rule_add"),
    path("rules/<int:pk>/edit/", views.PenaltyRuleUpdateView.as_view(), name="rule_edit"),
    path("employee/<int:pk>/", views.PenaltyHistoryView.as_view(), name="employee_history"),
]
