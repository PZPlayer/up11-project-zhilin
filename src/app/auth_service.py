from db import db_cursor
from errors import AppError
from models import User


def login(login_text):
    """Вход только по логину (без пароля). Неизвестный логин -> AppError."""
    login_text = (login_text or "").strip()
    if not login_text:
        raise AppError("Введите логин. Для просмотра каталога без входа выберите «Продолжить как гость».")
    with db_cursor() as cur:
        cur.execute("""
            SELECT u.id, u.login, u.last_name, u.first_name, u.middle_name, r.name
            FROM users u JOIN roles r ON r.id = u.role_id
            WHERE u.login = %s
        """, (login_text,))
        row = cur.fetchone()
    if not row:
        raise AppError(f"Пользователь с логином «{login_text}» не найден. "
                       f"Проверьте логин или продолжите как гость.")
    return User(*row)
