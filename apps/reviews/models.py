import uuid
from django.db import models
from django.conf import settings

from apps.common.models import BaseModel


class Tag(BaseModel):
    """Review tag to reflect mood (e.g., Happy, Disappointed, Neutral)."""

    MOOD_CHOICES = [
        ("positive", "Positive"),
        ("neutral", "Neutral"),
        ("negative", "Negative"),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default="neutral")

    class Meta:
        verbose_name_plural = "tags"
        ordering = ["mood", "name"]

    def __str__(self):
        return self.name


class Review(BaseModel):
    """User review/experience."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="reviews",
        blank=True
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="reviews",
        help_text="Company this review is about"
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)]
    )
    faced_company = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When you faced/interacted with the company"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending"
    )
    is_hidden = models.BooleanField(default=False, help_text="User can hide their own review")
    comments_enabled = models.BooleanField(default=True, help_text="Allow comments on this review")
    evidence = models.FileField(upload_to="reviews/evidence/", blank=True)
    thumbnail = models.ImageField(upload_to="reviews/thumbnails/", blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return self.title


class ReviewUpdate(BaseModel):
    """Update/pinned message on a review by the author."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="updates"
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="review_updates",
        blank=True,
        help_text="Additional tags to add to the review"
    )
    message = models.TextField(help_text="Update message from the author")
    photos = models.ImageField(upload_to="reviews/updates/", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Update on {self.review.title}"


class Comment(BaseModel):
    """Comment on a review."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments",
        help_text="Optional tag to enforce or decrease the initial tag"
    )
    message = models.TextField()
    photos = models.ImageField(upload_to="comments/photos/", blank=True)
    is_company_response = models.BooleanField(
        default=False,
        help_text="This comment is an official response from the company"
    )
    is_company_response = models.BooleanField(
        default=False,
        help_text="True if this is an official response from the company"
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["review", "-created_at"]),
        ]

    def __str__(self):
        user_name = self.user.full_name or str(self.user.phone)
        return f"Comment by {user_name} on {self.review.title}"

    @property
    def is_reply(self):
        return self.parent is not None
