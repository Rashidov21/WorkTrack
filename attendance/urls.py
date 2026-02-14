from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("logs/", views.AttendanceLogListView.as_view(), name="log_list"),
    path("logs/<int:pk>/delete/", views.AttendanceLogDeleteView.as_view(), name="log_delete"),
    path("summary/", views.DailySummaryListView.as_view(), name="summary_list"),
]
