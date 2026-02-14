from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import UzbekLoginForm

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html", redirect_authenticated_user=True, form_class=UzbekLoginForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
