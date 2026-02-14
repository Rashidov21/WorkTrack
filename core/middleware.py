"""Custom middleware."""
from django.conf import settings
from .utils import audit_log


class AuditLogMiddleware:
    """Log authenticated user actions (optional; can be extended)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(settings, "AUDIT_LOG_ENABLED", False) and request.user.is_authenticated:
            # Optional: log POST/PUT/DELETE to sensitive paths
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and "/admin/" not in request.path:
                audit_log(
                    user=request.user,
                    action=request.method,
                    message=f"{request.method} {request.path}",
                    request=request,
                )
        return response
