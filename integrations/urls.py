from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("webhook/", views.DeviceWebhookView.as_view(), name="webhook"),
    path("settings/", views.IntegrationSettingsView.as_view(), name="settings"),
    path("settings/platform/", views.PlatformSettingsView.as_view(), name="platform_settings"),
]
