from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange

COVER_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp"]

REVIEW_RATING_CHOICES = [
    (5, "5 — отлично"),
    (4, "4 — хорошо"),
    (3, "3 — удовлетворительно"),
    (2, "2 — неудовлетворительно"),
    (1, "1 — плохо"),
    (0, "0 — ужасно"),
]


class LoginForm(FlaskForm):
    login = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class BookForm(FlaskForm):
    """Базовая форма книги. Используется как для добавления, так и для редактирования."""

    title = StringField("Название", validators=[DataRequired(), Length(max=255)])
    description = TextAreaField("Краткое описание", validators=[DataRequired()])
    year = IntegerField("Год", validators=[DataRequired(), NumberRange(min=0, max=2100)])
    publisher = StringField("Издательство", validators=[DataRequired(), Length(max=255)])
    author = StringField("Автор", validators=[DataRequired(), Length(max=255)])
    pages = IntegerField("Объём (страниц)", validators=[DataRequired(), NumberRange(min=1)])
    genres = SelectMultipleField("Жанр", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class BookCreateForm(BookForm):
    """Форма добавления книги — дополнительно содержит поле загрузки обложки."""

    cover = FileField(
        "Обложка",
        validators=[
            FileRequired("Необходимо выбрать файл обложки"),
            FileAllowed(COVER_EXTENSIONS, "Разрешены только изображения"),
        ],
    )


class ReviewForm(FlaskForm):
    rating = SelectField(
        "Оценка", choices=REVIEW_RATING_CHOICES, coerce=int, default=5, validators=[DataRequired()]
    )
    text = TextAreaField("Текст рецензии", validators=[DataRequired()])
    submit = SubmitField("Сохранить")
