"""Attendance logs and daily summaries."""
from django.db import models
from django.utils import timezone


class AttendanceLog(models.Model):
    """Raw check-in/check-out event from device or manual entry."""
    EVENT_CHOICES = [
        ("check_in", "Kelish"),
        ("check_out", "Ketish"),
    ]
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="attendance_logs",
    )
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    # Idempotency: device event ID to avoid duplicates
    source_id = models.CharField(max_length=255, blank=True, db_index=True)
    source = models.CharField(max_length=50, default="device", help_text="device, manual, api")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_id"],
                condition=models.Q(source_id__gt=""),
                name="attendance_unique_source_id",
            ),
        ]
        indexes = [
            models.Index(fields=["employee", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
        verbose_name = "Attendance Log"
        verbose_name_plural = "Attendance Logs"

    def __str__(self):
        return f"{self.employee_id} {self.event_type} @ {self.timestamp}"


class DailySummary(models.Model):
    """Per-employee per-day summary: status, hours, late minutes."""
    STATUS_PRESENT = "present"
    STATUS_LATE = "late"
    STATUS_ABSENT = "absent"
    STATUS_LEAVE = "leave"
    STATUS_CHOICES = [
        (STATUS_PRESENT, "Keldi"),
        (STATUS_LATE, "Kechikdi"),
        (STATUS_ABSENT, "Kelmadi"),
        (STATUS_LEAVE, "Ta'tilda"),
    ]

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="daily_summaries",
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ABSENT)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    working_minutes = models.PositiveIntegerField(default=0)
    minutes_late = models.PositiveIntegerField(default=0)
    missing_check_out = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee"]
        unique_together = [["employee", "date"]]
        verbose_name = "Daily Summary"
        verbose_name_plural = "Daily Summaries"

    def __str__(self):
        return f"{self.employee} {self.date} {self.status}"


class LatenessRecord(models.Model):
    """One lateness occurrence: employee, date, minutes late."""
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="lateness_records",
    )
    date = models.DateField(db_index=True)
    minutes_late = models.PositiveIntegerField()
    check_in_time = models.DateTimeField()
    expected_start = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Lateness Record"
        verbose_name_plural = "Lateness Records"

    def __str__(self):
        return f"{self.employee} {self.date} ({self.minutes_late} min late)"
