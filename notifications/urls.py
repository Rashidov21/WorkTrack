from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("telegram/", views.TelegramSettingsView.as_view(), name="telegram_settings"),
]
