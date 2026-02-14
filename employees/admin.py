from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["employee_id", "first_name", "last_name", "department", "work_start_time", "is_active"]
    list_filter = ["is_active", "department"]
    search_fields = ["employee_id", "first_name", "last_name"]
