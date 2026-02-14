"""Custom decorators for role-based access."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Require user to have one of the given roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not hasattr(request.user, "role") or request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def admin_required(view_func):
    """Require admin role."""
    return role_required("admin")(view_func)


def manager_required(view_func):
    """Require manager, admin or viewer (view reports and lists; edit restricted in templates)."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not hasattr(request.user, "role"):
            raise PermissionDenied
        if request.user.role not in ("admin", "manager", "viewer"):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped
