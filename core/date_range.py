"""Umumiy sana oralig‘i: GET parametrlaridan start/end."""
from datetime import date, timedelta

from django.utils import timezone

# Juda katta eksportlarni cheklash
MAX_DATE_RANGE_DAYS = 366


def parse_date_range(request, *, default_period="month"):
    """
    GET: date_from, date_to (YYYY-MM-DD) — ustun.
    Aks holda: period = day | week | month | year (default_period).
    attendance/logs uchun: eski `date` bitta kun.
    Qaytaradi: (start, end, mode) — mode: 'custom' | 'day' | 'week' | 'month' | 'year'
    """
    today = timezone.now().date()
    g = request.GET

    df = (g.get("date_from") or "").strip()
    dt = (g.get("date_to") or "").strip()

    # Eski log: bitta kun
    legacy = (g.get("date") or "").strip()
    if legacy and not df and not dt:
        try:
            d = date.fromisoformat(legacy)
            return d, d, "day"
        except ValueError:
            pass

    if df or dt:
        if df and not dt:
            dt = df
        if dt and not df:
            df = dt
        try:
            start = date.fromisoformat(df)
            end = date.fromisoformat(dt)
        except ValueError:
            start = end = today
        if start > end:
            start, end = end, start
        span = (end - start).days
        if span > MAX_DATE_RANGE_DAYS:
            end = start + timedelta(days=MAX_DATE_RANGE_DAYS)
        return start, end, "custom"

    period = (g.get("period") or default_period).strip()
    if period not in ("day", "week", "month", "year"):
        period = default_period if default_period in ("day", "week", "month", "year") else "month"

    end = today
    if period == "day":
        start = end
    elif period == "week":
        start = end - timedelta(days=6)
    elif period == "month":
        start = end.replace(day=1)
    else:  # year
        start = end.replace(month=1, day=1)

    return start, end, period


def query_string_for_export(request, allowed_keys=None):
    """Excel havolasi uchun GET ni nusxalash."""
    from urllib.parse import urlencode

    if allowed_keys is None:
        allowed_keys = {
            "date_from",
            "date_to",
            "period",
            "employee_id",
            "event_type",
        }
    data = {}
    for k in request.GET:
        if k not in allowed_keys:
            continue
        v = request.GET.get(k)
        if v is not None and str(v).strip() != "":
            data[k] = v
    return urlencode(data)
