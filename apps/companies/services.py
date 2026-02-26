"""Company business logic - write operations."""
from django.utils import timezone
from django.db import transaction

from .models import Company, CompanyClaim
from apps.reviews.services import sanitize_body


def sanitize_message(message: str) -> str:
    """Sanitize company response message."""
    allowed_tags = ["b", "i", "em", "strong", "p", "br"]
    return sanitize_body(message, allowed_tags=allowed_tags)


@transaction.atomic
def claim_request_create(
    user,
    company,
    verification_method,
    verification_email="",
    verification_document=None,
    verification_website_code="",
    requester_name="",
    requester_role="",
    requester_notes=""
):
    """
    Submit a claim request for an existing company.

    Args:
        user: The User submitting the claim
        company: The Company to claim
        verification_method: Method of verification
        verification_email: Company email for verification
        verification_document: File upload
        verification_website_code: Code from website
        requester_name: Name of the requester
        requester_role: Role at the company
        requester_notes: Additional notes

    Returns:
        CompanyClaim instance
    """
    # Check if user already has a claimed company (one company per account)
    if hasattr(user, 'claimed_company') and user.claimed_company:
        raise ValueError("You already have a claimed company. Each account can only claim one company.")

    # Check if company is already claimed
    if company.claimed_by:
        raise ValueError("This company has already been claimed")

    # Check if user has pending claim for this company
    existing_claim = CompanyClaim.objects.filter(
        user=user,
        company=company,
        status=CompanyClaim.Status.PENDING
    ).exists()

    if existing_claim:
        raise ValueError("You already have a pending claim for this company")

    claim = CompanyClaim.objects.create(
        user=user,
        company=company,
        verification_method=verification_method,
        verification_email=verification_email,
        verification_document=verification_document,
        verification_website_code=verification_website_code,
        requester_name=requester_name,
        requester_role=requester_role,
        requester_notes=requester_notes
    )

    return claim


@transaction.atomic
def claim_request_create_new_company(
    user,
    company_data,
    verification_method,
    verification_email="",
    verification_document=None,
    verification_website_code="",
    requester_name="",
    requester_role="",
    requester_notes=""
):
    """
    Create a new company and submit a claim request.

    Args:
        user: The User submitting the claim
        company_data: Dict with company fields
        verification_method: Method of verification
        verification_email: Company email
        verification_document: File upload
        verification_website_code: Code from website
        requester_name: Name of requester
        requester_role: Role at company
        requester_notes: Additional notes

    Returns:
        tuple: (Company, CompanyClaim)
    """
    # Check if user already has a claimed company (one company per account)
    if hasattr(user, 'claimed_company') and user.claimed_company:
        raise ValueError("You already have a claimed company. Each account can only claim one company.")

    company = Company.objects.create(**company_data)

    claim = CompanyClaim.objects.create(
        user=user,
        company=company,
        verification_method=verification_method,
        verification_email=verification_email,
        verification_document=verification_document,
        verification_website_code=verification_website_code,
        requester_name=requester_name,
        requester_role=requester_role,
        requester_notes=requester_notes
    )

    return company, claim


@transaction.atomic
def claim_approve(claim, admin_user):
    """
    Approve a company claim request.

    Args:
        claim: CompanyClaim instance to approve
        admin_user: The admin user approving

    Returns:
        Updated CompanyClaim instance
    """
    if claim.status != CompanyClaim.Status.PENDING:
        raise ValueError("Only pending claims can be approved")

    claim.status = CompanyClaim.Status.APPROVED
    claim.reviewed_by = admin_user
    claim.reviewed_at = timezone.now()
    claim.save()

    company = claim.company
    company.is_verified = True
    company.verified_at = timezone.now()
    company.claimed_by = claim.user
    company.save()

    return claim


@transaction.atomic
def claim_reject(claim, admin_user, rejection_reason):
    """
    Reject a company claim request.

    Args:
        claim: CompanyClaim instance to reject
        admin_user: The admin user rejecting
        rejection_reason: Reason for rejection

    Returns:
        Updated CompanyClaim instance
    """
    if claim.status != CompanyClaim.Status.PENDING:
        raise ValueError("Only pending claims can be rejected")

    if not rejection_reason:
        raise ValueError("Rejection reason is required")

    claim.status = CompanyClaim.Status.REJECTED
    claim.reviewed_by = admin_user
    claim.reviewed_at = timezone.now()
    claim.rejection_reason = rejection_reason
    claim.save()

    return claim


def company_respond_to_review(company_user, review, message):
    """
    Allow a company to respond to a review.

    Args:
        company_user: The User with claimed company
        review: The Review to respond to
        message: The response message

    Returns:
        Comment instance
    """
    if not hasattr(company_user, 'claimed_company') or not company_user.claimed_company:
        raise ValueError("You must have a verified company account to respond to reviews")

    company = company_user.claimed_company

    if review.company != company:
        raise ValueError("You can only respond to reviews about your company")

    if not company.is_verified:
        raise ValueError("Your company must be verified to respond to reviews")

    sanitized_message = sanitize_message(message)

    from apps.reviews.models import Comment
    comment = Comment.objects.create(
        user=company_user,
        review=review,
        message=sanitized_message,
        is_company_response=True
    )

    return comment
