import hashlib
import os
import shutil

import click

from app.extensions import db
from app.models import Book, Cover, Genre, Review, ReviewStatus, Role, User

SEED_COVERS_DIR = os.path.join(os.path.dirname(__file__), "static", "seed_covers")

ROLES = [
    ("admin", "Администратор", "Полный доступ к системе, в том числе создание и удаление книг."),
    ("moderator", "Модератор", "Редактирование данных книг и модерация рецензий."),
    ("user", "Пользователь", "Может оставлять рецензии на книги."),
]

REVIEW_STATUSES = [
    ("pending", "На рассмотрении", "Рецензия отправлена и ожидает решения модератора."),
    ("approved", "Одобрено", "Рецензия прошла модерацию и отображается на странице книги."),
    ("rejected", "Отклонено", "Рецензия не прошла модерацию."),
]

GENRES = ["Роман", "Фантастика", "Детектив", "Поэзия", "Классика", "Драма"]

USERS = [
    ("admin", "admin123", "Иванов", "Иван", "Иванович", "admin"),
    ("moderator", "moderator123", "Петров", "Пётр", "Петрович", "moderator"),
    ("user", "user123", "Сидоров", "Сидор", "Сидорович", "user"),
]

BOOKS = [
    {
        "title": "Война и мир",
        "description": "Роман-эпопея, описывающий русское общество в эпоху войн против Наполеона.",
        "year": 1869,
        "publisher": "Русский вестник",
        "author": "Лев Толстой",
        "pages": 1300,
        "genres": ["Роман", "Классика", "Драма"],
        "cover": "book1.jpg",
    },
    {
        "title": "Преступление и наказание",
        "description": "История о душевных терзаниях бывшего студента, решившегося на убийство.",
        "year": 1866,
        "publisher": "Русский вестник",
        "author": "Фёдор Достоевский",
        "pages": 671,
        "genres": ["Роман", "Классика", "Детектив"],
        "cover": "book2.jpg",
    },
    {
        "title": "Мастер и Маргарита",
        "description": "Мистический роман о визите дьявола в Москву и любви Мастера и Маргариты.",
        "year": 1967,
        "publisher": "Художественная литература",
        "author": "Михаил Булгаков",
        "pages": 480,
        "genres": ["Роман", "Фантастика", "Классика"],
        "cover": "book3.jpg",
    },
    {
        "title": "Отцы и дети",
        "description": "Роман о конфликте поколений и идейных течений в русском обществе XIX века.",
        "year": 1862,
        "publisher": "Русский вестник",
        "author": "Иван Тургенев",
        "pages": 280,
        "genres": ["Роман", "Классика", "Драма"],
        "cover": "book4.jpg",
    },
    {
        "title": "Евгений Онегин",
        "description": "Роман в стихах, одно из величайших произведений русской литературы.",
        "year": 1833,
        "publisher": "Художественная литература",
        "author": "Александр Пушкин",
        "pages": 320,
        "genres": ["Роман", "Поэзия", "Классика"],
        "cover": "book5.jpg",
    },
]


def _save_seed_cover(filename, book, upload_folder):
    src_path = os.path.join(SEED_COVERS_DIR, filename)
    with open(src_path, "rb") as f:
        file_bytes = f.read()

    digest = hashlib.md5(file_bytes).hexdigest()
    extension = filename.rsplit(".", 1)[-1].lower()

    cover = Cover(filename="", mime_type="image/jpeg", md5_hash=digest, book_id=book.id)
    db.session.add(cover)
    db.session.flush()

    cover.filename = f"{cover.id}.{extension}"
    shutil.copyfile(src_path, os.path.join(upload_folder, cover.filename))


def seed_database(app):
    with app.app_context():
        if Role.query.first() is not None:
            click.echo("База данных уже содержит данные, сидинг пропущен.")
            return

        roles = {}
        for code, name, description in ROLES:
            role = Role(code=code, name=name, description=description)
            db.session.add(role)
            roles[code] = role

        statuses = {}
        for code, name, description in REVIEW_STATUSES:
            status = ReviewStatus(code=code, name=name, description=description)
            db.session.add(status)
            statuses[code] = status

        genres = {}
        for name in GENRES:
            genre = Genre(name=name)
            db.session.add(genre)
            genres[name] = genre

        db.session.flush()

        for login, password, last_name, first_name, middle_name, role_code in USERS:
            user = User(
                login=login,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                role=roles[role_code],
            )
            user.set_password(password)
            db.session.add(user)

        db.session.flush()

        for data in BOOKS:
            book = Book(
                title=data["title"],
                description=data["description"],
                year=data["year"],
                publisher=data["publisher"],
                author=data["author"],
                pages=data["pages"],
            )
            book.genres = [genres[name] for name in data["genres"]]
            db.session.add(book)
            db.session.flush()

            _save_seed_cover(data["cover"], book, app.config["UPLOAD_FOLDER"])

        db.session.flush()

        sample_user = User.query.filter_by(login="user").first()
        war_and_peace = Book.query.filter_by(title="Война и мир").first()
        master_margarita = Book.query.filter_by(title="Мастер и Маргарита").first()

        db.session.add(
            Review(
                book=war_and_peace,
                user=sample_user,
                rating=5,
                text="Великое произведение, которое стоит прочитать каждому.",
                status=statuses["approved"],
            )
        )
        db.session.add(
            Review(
                book=master_margarita,
                user=sample_user,
                rating=4,
                text="Очень атмосферная книга, но концовка показалась скомканной.",
                status=statuses["pending"],
            )
        )

        db.session.commit()
        click.echo("База данных успешно заполнена тестовыми данными.")


def register(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Создать таблицы базы данных."""
        with app.app_context():
            db.create_all()
        click.echo("Таблицы базы данных созданы.")

    @app.cli.command("seed-db")
    def seed_db_command():
        """Заполнить базу данных ролями, статусами, жанрами, пользователями и демо-книгами."""
        seed_database(app)
