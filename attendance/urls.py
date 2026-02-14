from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("logs/", views.AttendanceLogListView.as_view(), name="log_list"),
    path("summary/", views.DailySummaryListView.as_view(), name="summary_list"),
]
