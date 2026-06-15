import hashlib
import os

from flask import current_app, flash, redirect, render_template, url_for
from flask_login import current_user

from app.auth.decorators import role_required
from app.books import bp
from app.extensions import db
from app.forms import BookCreateForm, BookForm
from app.models import Book, Cover, Genre
from app.utils import sanitize_text


def _populate_genre_choices(form):
    form.genres.choices = [(g.id, g.name) for g in Genre.query.order_by(Genre.name).all()]


def _save_cover(file_storage, book):
    """Сохраняет запись об обложке в БД с дедупликацией по MD5.

    Возвращает кортеж (cover, file_bytes_to_write). Если файл с таким же
    MD5-хэшем уже был загружен ранее, file_bytes_to_write будет None —
    повторно сохранять файл на диск не нужно.
    """
    file_bytes = file_storage.read()
    digest = hashlib.md5(file_bytes).hexdigest()

    existing = Cover.query.filter_by(md5_hash=digest).first()

    extension = file_storage.filename.rsplit(".", 1)[-1].lower()

    if existing is not None:
        cover = Cover(
            filename=existing.filename,
            mime_type=existing.mime_type,
            md5_hash=digest,
            book_id=book.id,
        )
        db.session.add(cover)
        return cover, None

    cover = Cover(filename="", mime_type=file_storage.mimetype, md5_hash=digest, book_id=book.id)
    db.session.add(cover)
    db.session.flush()  # нужен cover.id для имени файла

    cover.filename = f"{cover.id}.{extension}"
    return cover, file_bytes


def _write_cover_file(filename, file_bytes):
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    with open(path, "wb") as f:
        f.write(file_bytes)


def _delete_cover_file(filename):
    """Удаляет файл обложки, только если он больше не используется другими записями."""
    other = Cover.query.filter_by(filename=filename).first()
    if other is not None:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)


@bp.route("/<int:book_id>")
def view(book_id):
    book = Book.query.get_or_404(book_id)

    user_review = None
    if current_user.is_authenticated:
        user_review = next((r for r in book.reviews if r.user_id == current_user.id), None)

    can_review = (
        current_user.is_authenticated
        and current_user.has_role("user", "moderator", "admin")
        and user_review is None
    )

    approved_reviews = sorted(book.approved_reviews, key=lambda r: r.created_at, reverse=True)

    return render_template(
        "books/view.html",
        book=book,
        reviews=approved_reviews,
        user_review=user_review,
        can_review=can_review,
    )


@bp.route("/add", methods=["GET", "POST"])
@role_required("admin")
def add():
    form = BookCreateForm()
    _populate_genre_choices(form)

    if form.validate_on_submit():
        book = Book(
            title=form.title.data.strip(),
            description=sanitize_text(form.description.data),
            year=form.year.data,
            publisher=form.publisher.data.strip(),
            author=form.author.data.strip(),
            pages=form.pages.data,
        )
        book.genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()

        try:
            db.session.add(book)
            db.session.flush()  # получаем book.id (аналог lastrowid)

            cover, file_bytes = _save_cover(form.cover.data, book)

            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                "danger",
            )
            return render_template("books/form.html", form=form, is_edit=False)

        if file_bytes is not None:
            _write_cover_file(cover.filename, file_bytes)

        flash("Книга успешно добавлена.", "success")
        return redirect(url_for("books.view", book_id=book.id))

    return render_template("books/form.html", form=form, is_edit=False)


@bp.route("/<int:book_id>/edit", methods=["GET", "POST"])
@role_required("admin", "moderator")
def edit(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    _populate_genre_choices(form)

    if form.validate_on_submit():
        book.title = form.title.data.strip()
        book.description = sanitize_text(form.description.data)
        book.year = form.year.data
        book.publisher = form.publisher.data.strip()
        book.author = form.author.data.strip()
        book.pages = form.pages.data
        book.genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                "danger",
            )
            return render_template("books/form.html", form=form, is_edit=True, book=book)

        flash("Данные книги успешно обновлены.", "success")
        return redirect(url_for("books.view", book_id=book.id))

    if not form.is_submitted():
        form.genres.data = [g.id for g in book.genres]

    return render_template("books/form.html", form=form, is_edit=True, book=book)


@bp.route("/<int:book_id>/delete", methods=["POST"])
@role_required("admin")
def delete(book_id):
    book = Book.query.get_or_404(book_id)
    title = book.title
    cover_filename = book.cover.filename if book.cover is not None else None

    try:
        db.session.delete(book)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("При удалении книги возникла ошибка.", "danger")
        return redirect(url_for("main.index"))

    if cover_filename is not None:
        _delete_cover_file(cover_filename)

    flash(f"Книга «{title}» успешно удалена.", "success")
    return redirect(url_for("main.index"))
