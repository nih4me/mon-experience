import uuid
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
            # Try to find existing company with same name and country
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
        # Normalize name for consistency
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)
