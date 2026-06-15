import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "library.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads", "covers")
    ALLOWED_COVER_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    BOOKS_PER_PAGE = 10
    REVIEWS_PER_PAGE = 10
