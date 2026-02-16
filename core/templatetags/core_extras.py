"""Template filters: UZS formatting and similar."""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def format_uzs(value):
    """Format number as UZS: space as thousand separator + ' so'm'. E.g. 1 234 567 so'm."""
    if value is None:
        return ""
    try:
        num = int(value)
    except (ValueError, TypeError):
        try:
            num = int(float(value))
        except (ValueError, TypeError):
            return str(value)
    s = f"{num:,}".replace(",", " ")
    return mark_safe(f"{s} so'm")
