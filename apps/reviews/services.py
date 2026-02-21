import bleach
from django.db import transaction

from apps.reviews.models import Tag

ALLOWED_TAGS = ["b", "i", "em", "strong", "p", "ul", "ol", "li"]


def sanitize_body(raw_html: str) -> str:
    """Sanitize HTML content using bleach."""
    return bleach.clean(raw_html, tags=ALLOWED_TAGS, strip=True)


@transaction.atomic
def tag_create(*, name: str, slug: str, description: str = "", mood: str = "neutral") -> Tag:
    """Create a new tag."""
    return Tag.objects.create(name=name, slug=slug, description=description, mood=mood)


def tag_get(*, slug: str) -> Tag | None:
    """Get tag by slug."""
    return Tag.objects.filter(slug=slug).first()


def tag_list() -> list[Tag]:
    """List all tags."""
    return list(Tag.objects.all())
