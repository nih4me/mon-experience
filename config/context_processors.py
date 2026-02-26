"""Custom context processors for the project."""
from apps.companies.selectors import company_get_for_user


def company_context(request):
    """Add claimed company to context for authenticated users."""
    if request.user.is_authenticated:
        claimed_company = company_get_for_user(request.user)
        return {
            'claimed_company': claimed_company,
        }
    return {}
