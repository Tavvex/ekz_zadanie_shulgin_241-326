from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

NO_AUTH_MESSAGE = "Для выполнения данного действия необходимо пройти процедуру аутентификации."
NO_PERMISSION_MESSAGE = "У вас недостаточно прав для выполнения данного действия."


def role_required(*role_codes):
    """Доступ только для аутентифицированных пользователей с одной из указанных ролей."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash(NO_AUTH_MESSAGE, "warning")
                return redirect(url_for("auth.login"))
            if not current_user.has_role(*role_codes):
                flash(NO_PERMISSION_MESSAGE, "danger")
                return redirect(url_for("main.index"))
            return view(*args, **kwargs)

        return wrapped

    return decorator
