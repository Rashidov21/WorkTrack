"""Login, logout, profile."""
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse_lazy


class LoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("core:dashboard")


class LogoutView(LogoutView):
    next_page = "accounts:login"


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
