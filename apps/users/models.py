import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """Custom user model with UUID primary key, phone auth, and full name."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="users/avatars/", blank=True)
    country = CountryField()
    phone = PhoneNumberField(
        unique=True,
        region=None,
        help_text="Phone number with country code (e.g., +1234567890)"
    )
    full_name = models.CharField(max_length=150, blank=True, verbose_name="Full Name")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Remove username - use phone for authentication
    username = None

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.full_name or str(self.phone)
