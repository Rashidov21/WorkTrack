from django.urls import path
from . import views

app_name = "integrations"

urlpatterns = [
    path("webhook/", views.DeviceWebhookView.as_view(), name="webhook"),
    path("settings/", views.IntegrationSettingsView.as_view(), name="settings"),
    path("settings/platform/", views.PlatformSettingsView.as_view(), name="platform_settings"),
    path("events/unmatched/", views.UnmatchedEventsView.as_view(), name="unmatched_events"),
    path("events/<int:pk>/resolve/", views.ResolveRawEventView.as_view(), name="resolve_raw_event"),
    path("events/<int:pk>/replay/", views.ReplayRawEventView.as_view(), name="replay_raw_event"),
]
