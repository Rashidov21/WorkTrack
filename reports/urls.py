from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportDashboardView.as_view(), name="dashboard"),
    path("attendance/", views.ReportAttendanceView.as_view(), name="attendance"),
    path("lateness/", views.ReportLatenessView.as_view(), name="lateness"),
    path("penalty/", views.ReportPenaltyView.as_view(), name="penalty"),
    path("export/attendance/", views.ExportAttendanceExcelView.as_view(), name="export_attendance"),
    path("export/lateness/", views.ExportLatenessExcelView.as_view(), name="export_lateness"),
    path("export/penalty/", views.ExportPenaltyExcelView.as_view(), name="export_penalty"),
]
