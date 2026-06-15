from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.auth.decorators import role_required
from app.extensions import db
from app.forms import ReviewForm
from app.models import Book, Review, ReviewStatus
from app.reviews import bp
from app.utils import sanitize_text


@bp.route("/books/<int:book_id>/review", methods=["GET", "POST"])
@role_required("user", "moderator", "admin")
def create(book_id):
    book = Book.query.get_or_404(book_id)

    existing = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()
    if existing is not None:
        flash("Вы уже оставили рецензию на эту книгу.", "info")
        return redirect(url_for("books.view", book_id=book.id))

    form = ReviewForm()

    if form.validate_on_submit():
        pending_status = ReviewStatus.query.filter_by(code="pending").first()

        review = Review(
            book_id=book.id,
            user_id=current_user.id,
            rating=form.rating.data,
            text=sanitize_text(form.text.data),
            status=pending_status,
        )

        try:
            db.session.add(review)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                "danger",
            )
            return render_template("reviews/form.html", form=form, book=book)

        flash("Рецензия отправлена на модерацию.", "success")
        return redirect(url_for("books.view", book_id=book.id))

    return render_template("reviews/form.html", form=form, book=book)


@bp.route("/my-reviews")
@role_required("user")
def my_reviews():
    reviews = (
        Review.query.filter_by(user_id=current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return render_template("reviews/my_reviews.html", reviews=reviews)


@bp.route("/moderation")
@role_required("moderator")
def moderation_list():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Review.query.join(ReviewStatus)
        .filter(ReviewStatus.code == "pending")
        .order_by(Review.created_at.asc())
        .paginate(page=page, per_page=current_app.config["REVIEWS_PER_PAGE"], error_out=False)
    )
    return render_template(
        "reviews/moderation_list.html", pagination=pagination, reviews=pagination.items
    )


@bp.route("/moderation/<int:review_id>")
@role_required("moderator")
def moderation_detail(review_id):
    review = Review.query.get_or_404(review_id)
    return render_template("reviews/moderation_detail.html", review=review)


@bp.route("/moderation/<int:review_id>/approve", methods=["POST"])
@role_required("moderator")
def approve(review_id):
    review = Review.query.get_or_404(review_id)
    review.status = ReviewStatus.query.filter_by(code="approved").first()
    db.session.commit()
    flash("Рецензия одобрена.", "success")
    return redirect(url_for("reviews.moderation_list"))


@bp.route("/moderation/<int:review_id>/reject", methods=["POST"])
@role_required("moderator")
def reject(review_id):
    review = Review.query.get_or_404(review_id)
    review.status = ReviewStatus.query.filter_by(code="rejected").first()
    db.session.commit()
    flash("Рецензия отклонена.", "success")
    return redirect(url_for("reviews.moderation_list"))
