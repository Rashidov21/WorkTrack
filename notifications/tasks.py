"""Celery task: send Telegram message."""
import requests
from celery import shared_task
from .models import TelegramSettings


@shared_task(bind=True, max_retries=3)
def send_telegram_message(self, text: str):
    """Send text to configured Telegram chat."""
    settings = TelegramSettings.get_settings()
    if not settings.enabled or not settings.bot_token or not settings.chat_id:
        return {"ok": False, "reason": "telegram_not_configured"}

    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {"chat_id": settings.chat_id, "text": text[:4096], "disable_web_page_preview": True}

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return {"ok": True}
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)
