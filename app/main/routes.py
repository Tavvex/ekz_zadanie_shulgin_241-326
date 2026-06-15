from flask import current_app, render_template, request

from app.main import bp
from app.models import Book


@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Book.query.order_by(Book.year.desc(), Book.id.desc()).paginate(
        page=page, per_page=current_app.config["BOOKS_PER_PAGE"], error_out=False
    )
    return render_template("index.html", pagination=pagination, books=pagination.items)
