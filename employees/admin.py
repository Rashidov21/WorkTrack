from django.contrib import admin
from .models import Employee, WorkSchedule


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ["name", "work_start_time", "work_end_time", "grace_period_minutes", "working_days", "is_active"]
    list_filter = ["is_active"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["employee_id", "first_name", "last_name", "department", "work_schedule", "work_start_time", "telegram_username", "is_active"]
    list_filter = ["is_active", "department", "work_schedule"]
    search_fields = ["employee_id", "first_name", "last_name", "telegram_username"]
