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
]
