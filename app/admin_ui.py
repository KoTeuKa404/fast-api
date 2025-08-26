# app/admin_ui.py
import os
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from app.db import engine
from app.models import User, Message

class AdminAuth(AuthenticationBackend):
    # приймаємо secret_key і передаємо базовому класу
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request) -> bool:
        # твоя логіка логіну (як у тебе було)
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        # повернути True якщо авторизація успішна
        # ...
        return True

    async def logout(self, request) -> bool:
        return True

    async def authenticate(self, request) -> bool:
        # перевірка сесії / куки
        # ...
        return True

def setup_admin(app) -> None:
    # візьми секрет із ENV, інакше — з SESSION_SECRET або дефолт
    secret = os.getenv("ADMIN_SECRET") or os.getenv("SESSION_SECRET") or "devsecret_change_me"

    admin = Admin(
        app,
        engine,
        authentication_backend=AdminAuth(secret_key=secret),
        base_url="/dashboard",
    )

    from sqladmin import ModelView

    class UserAdmin(ModelView, model=User):
        name_plural = "Users"
        column_list = [User.id, User.username, User.is_superuser, User.registered_at]

    class MessageAdmin(ModelView, model=Message):
        name_plural = "Messages"
        column_list = [Message.id, Message.username, Message.user_id, Message.timestamp, Message.edited]

    admin.add_view(UserAdmin)
    admin.add_view(MessageAdmin)
