"""Employee model: ID, department, work times, grace period, active status."""
from django.db import models


class Employee(models.Model):
    """Employee master data for attendance and penalties."""
    employee_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    # Work schedule (time only; date comes from attendance day)
    work_start_time = models.TimeField(help_text="Expected check-in time")
    work_end_time = models.TimeField(help_text="Expected check-out time")
    grace_period_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Minutes after work_start_time before considered late",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Optional: Hikvision person ID for device matching
    device_person_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["employee_id"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
