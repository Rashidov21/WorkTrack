"""Reusable utilities."""
from .models import AuditLog


def audit_log(user=None, action="", model_name="", object_id="", message="", request=None):
    """Create an audit log entry."""
    ip = None
    if request:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = (xff.split(",")[0].strip() if xff else None) or request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else "",
        message=message[:2000] if message else "",
        ip_address=ip,
    )
