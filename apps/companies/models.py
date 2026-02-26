import uuid
from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField


class CompanyManager(models.Manager):
    """Manager for Company with deduplication helpers."""

    def get_or_create_from_data(self, data: dict):
        """Get existing company or create new one based on name and country."""
        name = data.get("name", "").strip()
        country = data.get("country")

        if name and country:
            existing = self.filter(name__iexact=name, country=country).first()
            if existing:
                return existing, False

        return self.create(**data), True


class Company(models.Model):
    """Company model for storing company information."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    country = CountryField()
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = PhoneNumberField(region=None, blank=True, help_text="Company phone with country code")
    website = models.URLField(blank=True, help_text="Company website URL")
    industry = models.CharField(max_length=100, blank=True, help_text="Industry or sector")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Verification fields
    is_verified = models.BooleanField(default=False, help_text="Whether company has been verified")
    verified_at = models.DateTimeField(null=True, blank=True, help_text="When company was verified")
    claimed_by = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claimed_company",
        help_text="User who verified and manages this company account"
    )

    objects = CompanyManager()

    class Meta:
        db_table = "companies"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="unique_company_name_country")
        ]
        indexes = [
            models.Index(fields=["name", "country"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)


class CompanyClaim(models.Model):
    """Model for company claim/verification requests."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class VerificationMethod(models.TextChoices):
        EMAIL = "email", "Company Email"
        DOCUMENTS = "documents", "Business Documents"
        EMPLOYMENT = "employment", "Proof of Employment"
        WEBSITE = "website", "Website Verification"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_claims"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="claim_requests"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Verification details
    verification_method = models.CharField(
        max_length=20,
        choices=VerificationMethod.choices
    )
    verification_email = models.EmailField(
        blank=True,
        help_text="Company email for verification"
    )
    verification_document = models.FileField(
        upload_to="company_verification/documents/",
        blank=True,
        help_text="Upload business registration or authorization document"
    )
    verification_website_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="Verification code placed on company website"
    )

    # Additional info from requester
    requester_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Name of person submitting the claim"
    )
    requester_role = models.CharField(
        max_length=100,
        blank=True,
        help_text="Role/position of requester at company"
    )
    requester_notes = models.TextField(
        blank=True,
        help_text="Additional notes for verification"
    )

    # Admin review fields
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_claims"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the claim was reviewed"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection"
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for the review"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "company_claims"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "company"],
                name="unique_claim_per_company"
            )
        ]

    def __str__(self):
        return f"Claim by {self.user} for {self.company}"
