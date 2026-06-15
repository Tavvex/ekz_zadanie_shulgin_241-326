import os

from flask import Flask, flash, redirect, url_for
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config
from app.extensions import db, login_manager


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.utils import render_markdown

    app.jinja_env.filters["markdown"] = render_markdown

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        flash(
            "Для выполнения данного действия необходимо пройти процедуру аутентификации.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.books import bp as books_bp
    from app.reviews import bp as reviews_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(reviews_bp)

    from app import cli

    cli.register(app)

    return app
