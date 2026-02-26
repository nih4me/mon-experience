"""Company business logic - read operations (selectors)."""
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404

from .models import Company, CompanyClaim


def claim_request_get(claim_id):
    """Get a company claim by ID."""
    return get_object_or_404(CompanyClaim, id=claim_id)


def claim_request_list(status=None, user=None):
    """
    List company claims with optional filters.

    Args:
        status: Filter by status (pending/approved/rejected)
        user: Filter by user

    Returns:
        QuerySet of CompanyClaim
    """
    queryset = CompanyClaim.objects.all()

    if status:
        queryset = queryset.filter(status=status)

    if user:
        queryset = queryset.filter(user=user)

    return queryset.select_related('user', 'company', 'reviewed_by')


def claim_request_list_pending():
    """List all pending claims for admin review."""
    return claim_request_list(status=CompanyClaim.Status.PENDING)


def company_get_for_user(user):
    """
    Get the company associated with a user.

    Args:
        user: The User to get company for

    Returns:
        Company instance or None
    """
    if not user.is_authenticated:
        return None

    # Use direct query instead of hasattr for reliability
    try:
        return Company.objects.get(claimed_by=user)
    except Company.DoesNotExist:
        return None


def company_get_or_fail(company_id):
    """Get a company or raise 404."""
    return get_object_or_404(Company, id=company_id)


def company_list():
    """List all companies."""
    return Company.objects.all()


def company_list_verified():
    """List all verified companies."""
    return Company.objects.filter(is_verified=True)


def company_reviews_stats(company):
    """
    Get review statistics for a company.

    Args:
        company: Company instance

    Returns:
        dict with review counts and average rating
    """
    from apps.reviews.models import Review

    stats = Review.objects.filter(
        company=company,
        status='approved',
        is_hidden=False
    ).aggregate(
        total_reviews=Count('id'),
        avg_rating=Avg('rating')
    )

    return {
        'total_reviews': stats['total_reviews'] or 0,
        'avg_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
    }


def company_responses_for_review(review):
    """
    Get company responses for a review.

    Args:
        review: Review instance

    Returns:
        QuerySet of Comment (company responses)
    """
    from apps.reviews.models import Comment

    return Comment.objects.filter(
        review=review,
        is_company_response=True
    ).select_related('user')
