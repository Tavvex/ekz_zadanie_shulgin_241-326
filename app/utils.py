import bleach
import markdown as md

# Теги/атрибуты, которые могут появиться в HTML, сгенерированном из Markdown.
RENDERED_ALLOWED_TAGS = [
    "p", "br", "hr",
    "strong", "em", "del", "code", "pre", "blockquote",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
]

RENDERED_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}


def sanitize_text(text):
    """Удаляет все HTML-теги из пользовательского ввода перед сохранением в БД."""
    return bleach.clean(text or "", tags=[], attributes={}, strip=True)


def render_markdown(text):
    """Преобразует Markdown в HTML и очищает результат от потенциально опасных тегов."""
    html = md.markdown(text or "", extensions=["extra", "nl2br", "sane_lists"])
    return bleach.clean(html, tags=RENDERED_ALLOWED_TAGS, attributes=RENDERED_ALLOWED_ATTRS, strip=True)
