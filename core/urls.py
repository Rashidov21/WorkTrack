from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("settings/", views.SettingsRedirectView.as_view(), name="settings_redirect"),
    path("support/", views.SupportView.as_view(), name="support"),
]
