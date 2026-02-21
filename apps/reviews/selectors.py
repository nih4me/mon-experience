from apps.reviews.models import Category, Review


def category_get_or_fail(*, slug: str) -> Category:
    """Get category by slug or raise 404."""
    return Category.objects.get(slug=slug)


def review_list_select(*, status: str = "approved", category_slug: str = None) -> list[Review]:
    """List reviews with optional filters."""
    qs = Review.objects.filter(status=status)
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    return list(qs.select_related("user", "category"))


def review_get_select(*, id: str) -> Review | None:
    """Get review by ID with related data."""
    return Review.objects.select_related("user", "category").filter(id=id).first()
