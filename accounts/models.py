"""Custom user with role (admin, manager, viewer)."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("manager", "Menejer"),
        ("viewer", "Ko‘ruvchi"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="viewer")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == "admin"

    @property
    def is_manager_role(self):
        return self.role in ("admin", "manager")
