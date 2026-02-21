from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django_ratelimit.decorators import ratelimit

from apps.reviews.models import Review, Tag, Comment, ReviewUpdate
from apps.reviews.forms import ReviewForm, CommentForm, ReviewUpdateForm
from apps.reviews import services


# Home / Review List
class ReviewListView(ListView):
    """List all approved reviews."""

    model = Review
    template_name = "reviews/review_list.html"
    context_object_name = "reviews"
    paginate_by = 20

    def get_queryset(self):
        tag_slug = self.kwargs.get("tag_slug")
        # Exclude hidden reviews from public list
        qs = Review.objects.filter(
            status="approved",
            is_hidden=False
        ).select_related("user", "company").prefetch_related("tags")

        if tag_slug:
            return qs.filter(tags__slug=tag_slug)
        return qs


# Review Detail with Comments
class ReviewDetailView(DetailView):
    """Show review detail with comments."""

    model = Review
    template_name = "reviews/review_detail.html"
    context_object_name = "review"

    def get_queryset(self):
        return Review.objects.select_related("user", "company").prefetch_related("tags", "updates")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Hide hidden reviews from non-owners and non-staff
        if not (self.request.user.is_authenticated and (self.request.user == obj.user or self.request.user.is_staff)):
            if obj.is_hidden or obj.status != "approved":
                from django.http import Http404
                raise Http404("Review not found")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only show comment form if comments are enabled
        if self.request.user.is_authenticated and self.object.comments_enabled:
            context["comment_form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("user", "tag", "parent").prefetch_related("replies__user", "replies__tag").filter(parent__isnull=True)
        context["update_form"] = ReviewUpdateForm()
        context["updates"] = self.object.updates.select_related().prefetch_related("tags").all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Check if it's a comment or an update
        if "message" in request.POST and request.POST.get("update_form"):
            # Handle update form
            if request.user != self.object.user:
                messages.error(request, "Only the author can add updates.")
                return redirect("review_detail", pk=self.object.id)
            form = ReviewUpdateForm(request.POST, request.FILES)
            if form.is_valid():
                update = form.save(commit=False)
                update.review = self.object
                update.save()
                # Add tags to the update
                tags = form.cleaned_data.get("tags")
                if tags:
                    update.tags.set(tags)
                # Handle disable comments option
                if form.cleaned_data.get("disable_comments"):
                    self.object.comments_enabled = False
                    self.object.save()
                messages.success(request, "Update added successfully!")
        else:
            # Handle comment form
            if not self.object.comments_enabled:
                messages.error(request, "Comments are disabled for this review.")
                return redirect("review_detail", pk=self.object.id)
            form = CommentForm(request.POST, request.FILES)
            if form.is_valid() and request.user.is_authenticated:
                comment = form.save(commit=False)
                comment.user = request.user
                comment.review = self.object
                # Handle reply - parent_id is passed as UUID string in hidden input
                parent_id = form.cleaned_data.get("parent_id")
                if parent_id:
                    comment.parent_id = parent_id
                comment.save()
                messages.success(request, "Comment added successfully!" if not comment.parent else "Reply added successfully!")

        return redirect("review_detail", pk=self.object.id)


# Create Review (rate-limited for anonymous)
@ratelimit(key="ip", rate="5/h", method="POST", block=True)
@login_required
def review_create_view(request):
    """Create a new review."""
    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            # Set user on form instance before saving
            form.instance.user = request.user
            review = form.save()
            messages.success(request, "Review submitted successfully!")
            return redirect("review_detail", pk=review.id)
    else:
        form = ReviewForm()

    tags = services.tag_list()
    return render(request, "reviews/review_create.html", {
        "form": form,
        "tags": tags,
    })


# User's Reviews
@login_required
def my_reviews_view(request):
    """Show user's own reviews."""
    reviews = Review.objects.filter(user=request.user).select_related("company").prefetch_related("tags")
    return render(request, "reviews/my_reviews.html", {"reviews": reviews})


# Toggle Hide Review
@login_required
def toggle_hide_review(request, pk):
    """Toggle hide status of user's own review."""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    review.is_hidden = not review.is_hidden
    review.save()
    action = "hidden" if review.is_hidden else "visible"
    messages.success(request, f"Review is now {action}.")
    return redirect("my_reviews")


# Toggle Comments
@login_required
def toggle_comments(request, pk):
    """Toggle comments enabled status of user's own review."""
    review = get_object_or_404(Review, pk=pk, user=request.user)
    review.comments_enabled = not review.comments_enabled
    review.save()
    status = "enabled" if review.comments_enabled else "disabled"
    messages.success(request, f"Comments are now {status}.")
    return redirect("my_reviews")
