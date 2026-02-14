"""Template context processors."""
from django.conf import settings


def settings_context(request):
    """Expose minimal settings for templates (e.g. app name)."""
    return {
        "APP_NAME": "WorkTracker",
    }
