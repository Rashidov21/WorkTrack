from django.contrib import admin
from .models import AttendanceLog, DailySummary, LatenessRecord


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ["employee", "event_type", "timestamp", "source", "source_id"]
    list_filter = ["event_type", "source"]
    date_hierarchy = "timestamp"


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "status", "working_minutes", "minutes_late", "missing_check_out"]
    list_filter = ["status"]
    date_hierarchy = "date"


@admin.register(LatenessRecord)
class LatenessRecordAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "minutes_late", "check_in_time"]
    date_hierarchy = "date"
