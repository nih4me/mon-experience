"""Company views."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.paginator import Paginator

from .models import Company, CompanyClaim
from . import services, selectors
from .forms import ClaimRequestForm, NewCompanyWithClaimForm, CompanyResponseForm, AdminClaimReviewForm
from apps.reviews.models import Review
from apps.users.models import User


class CompanyAccountRequiredMixin(UserPassesTestMixin):
    """Mixin that requires user to have a verified company account."""

    def test_func(self):
        return hasattr(self.request.user, 'claimed_company') and self.request.user.claimed_company


def company_claim_request_view(request, company_id=None):
    """Submit a claim request for an existing company."""
    if not request.user.is_authenticated:
        messages.info(request, "Please login to claim a company")
        return redirect('login')

    # Check if user already has a claimed company
    company = selectors.company_get_for_user(request.user)
    if company:
        messages.warning(request, f"You already have a claimed company: {company.name}")
        return redirect('company_dashboard')

    # Get the company if company_id is provided
    preselected_company = None
    if company_id:
        try:
            preselected_company = Company.objects.get(id=company_id)
            if preselected_company.claimed_by:
                messages.error(request, "This company has already been claimed.")
                return redirect('review_list')
        except Company.DoesNotExist:
            messages.error(request, "Company not found.")
            return redirect('review_list')

    if request.method == 'POST':
        post_data = request.POST.copy()
        # If company is pre-selected, set it in POST data
        if preselected_company:
            post_data['existing_company'] = str(preselected_company.id)
        form = ClaimRequestForm(post_data, request.FILES, hide_company_field=bool(preselected_company))
        if form.is_valid():
            try:
                claim = form.save(request.user)
                messages.success(request, "Your claim request has been submitted. We'll review it shortly.")
                return redirect('company_dashboard')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        initial_data = {}
        if preselected_company:
            initial_data['existing_company'] = preselected_company
        form = ClaimRequestForm(initial=initial_data, hide_company_field=bool(preselected_company))

    return render(request, 'companies/claim_request_form.html', {
        'form': form,
        'page_title': 'Claim Company',
        'preselected_company': preselected_company,
        'company_name': preselected_company.name if preselected_company else None
    })


def company_register_and_claim_view(request):
    """Create a new company and submit a claim request with a new user account."""
    from django.contrib.auth import login
    from apps.users.models import User

    if request.method == 'POST':
        form = NewCompanyWithClaimForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create user account
                user = User.objects.create_user(
                    phone=form.cleaned_data['phone'],
                    email=form.cleaned_data['email'],
                    full_name=form.cleaned_data['full_name'],
                    country=form.cleaned_data.get('user_country'),
                    password=form.cleaned_data['password1']
                )

                # Log in the user
                login(request, user)

                # Create company and claim request
                company_data = {
                    'name': form.cleaned_data['name'],
                    'country': form.cleaned_data['country'],
                    'city': form.cleaned_data.get('city', ''),
                    'address': form.cleaned_data.get('address', ''),
                    'phone': form.cleaned_data.get('company_phone', ''),
                    'website': form.cleaned_data.get('website', ''),
                    'industry': form.cleaned_data.get('industry', ''),
                }
                company, claim = services.claim_request_create_new_company(
                    user=user,
                    company_data=company_data,
                    verification_method=form.cleaned_data['verification_method'],
                    verification_email=form.cleaned_data.get('verification_email', ''),
                    verification_document=form.cleaned_data.get('verification_document'),
                    verification_website_code=form.cleaned_data.get('verification_website_code', ''),
                    notes=form.cleaned_data.get('requester_notes', '')
                )
                messages.success(request, f"Company '{company.name}' has been registered. Your claim is pending review.")
                return redirect('company_dashboard')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = NewCompanyWithClaimForm()

    return render(request, 'companies/new_company_form.html', {
        'form': form,
        'page_title': 'Register Company'
    })


@login_required
def company_dashboard_view(request):
    """Company dashboard - view and respond to reviews."""
    company = selectors.company_get_for_user(request.user)

    if not company:
        messages.warning(request, "You don't have a claimed company yet.")
        return redirect('company_claim')

    # Get stats
    stats = selectors.company_reviews_stats(company)

    # Get reviews for this company
    reviews_list = Review.objects.filter(
        company=company,
        status='approved',
        is_hidden=False
    ).select_related('user').prefetch_related('tags')

    # Pagination
    paginator = Paginator(reviews_list, 10)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)

    # Handle response form
    response_form = None
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        if review_id:
            review = get_object_or_404(Review, id=review_id, company=company)
            response_form = CompanyResponseForm(request.POST)
            if response_form.is_valid():
                try:
                    services.company_respond_to_review(
                        request.user,
                        review,
                        response_form.cleaned_data['message']
                    )
                    messages.success(request, "Your response has been posted.")
                    return redirect('company_dashboard')
                except ValueError as e:
                    messages.error(request, str(e))

    # Get existing responses
    for review in reviews:
        review.company_responses = selectors.company_responses_for_review(review)

    return render(request, 'companies/dashboard.html', {
        'company': company,
        'stats': stats,
        'reviews': reviews,
        'response_form': response_form or CompanyResponseForm()
    })


# Admin views for claim management

@login_required
def admin_claim_list_view(request):
    """Admin view to list all claim requests."""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view this page.")
        return redirect('review_list')

    status_filter = request.GET.get('status')
    claims = selectors.claim_request_list(status=status_filter)

    paginator = Paginator(claims, 20)
    page_number = request.GET.get('page')
    claims_page = paginator.get_page(page_number)

    return render(request, 'companies/admin/claim_list.html', {
        'claims': claims_page,
        'status_filter': status_filter
    })


@login_required
def admin_claim_detail_view(request, claim_id):
    """Admin view to see claim details."""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view this page.")
        return redirect('review_list')

    claim = selectors.claim_request_get(claim_id)
    form = AdminClaimReviewForm(instance=claim)

    return render(request, 'companies/admin/claim_detail.html', {
        'claim': claim,
        'form': form
    })


@login_required
@require_http_methods(["POST"])
def admin_claim_approve_view(request, claim_id):
    """Admin view to approve a claim."""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('review_list')

    claim = selectors.claim_request_get(claim_id)

    try:
        services.claim_approve(claim, request.user)
        messages.success(request, f"Claim for {claim.company.name} has been approved.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('admin_claim_detail', claim_id=claim_id)


@login_required
@require_http_methods(["POST"])
def admin_claim_reject_view(request, claim_id):
    """Admin view to reject a claim."""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('review_list')

    claim = selectors.claim_request_get(claim_id)
    rejection_reason = request.POST.get('rejection_reason', '').strip()

    try:
        services.claim_reject(claim, request.user, rejection_reason)
        messages.success(request, f"Claim for {claim.company.name} has been rejected.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('admin_claim_detail', claim_id=claim_id)
