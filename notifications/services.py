"""Sync Telegram sender (no Celery)."""
import requests
from .models import TelegramSettings


def send_telegram_message_sync(text: str):
    """
    Telegram xabarini sync jo'natadi (Celery kerak emas).
    Returns {"ok": True} yoki {"ok": False, "reason": "..."} / {"ok": False, "error": "..."}.
    """
    settings = TelegramSettings.get_settings()
    if not settings.enabled or not settings.bot_token or not settings.chat_id:
        return {"ok": False, "reason": "telegram_not_configured"}
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {"chat_id": settings.chat_id, "text": text[:4096], "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
