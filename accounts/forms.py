from django.contrib.auth.forms import AuthenticationForm


class UzbekLoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Foydalanuvchi nomi yoki parol noto‘g‘ri. Iltimos, qaytadan urinib ko‘ring.",
        "inactive": "Bu hisob faol emas.",
    }
