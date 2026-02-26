from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from apps.reviews.models import Review, Tag, Comment, ReviewUpdate
from apps.companies.models import Company


class CompanyChoiceField(forms.ModelChoiceField):
    """Custom field that displays company name with country."""

    def label_from_instance(self, obj):
        return f"{obj.name} ({obj.country})"


class ReviewForm(forms.ModelForm):
    """Form for creating/editing reviews."""

    # Company selection
    existing_company = CompanyChoiceField(
        queryset=Company.objects.none(),
        required=False,
        empty_label="-- Select existing company --",
        help_text="Select an existing company or create a new one below"
    )

    # New company fields
    new_company_name = forms.CharField(
        max_length=255,
        required=False,
        label="New Company Name",
        help_text="Enter name for new company"
    )
    new_company_country = CountryField().formfield(
        required=False,
        label="New Company Country",
        help_text="Select country",
        widget=forms.Select(attrs={"class": "select2-single"})
    )
    new_company_city = forms.CharField(
        max_length=100,
        required=False,
        label="City"
    )
    new_company_address = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Address"
    )
    new_company_website = forms.URLField(
        required=False,
        label="Website"
    )
    new_company_industry = forms.CharField(
        max_length=100,
        required=False,
        label="Industry"
    )

    class Meta:
        model = Review
        fields = ["title", "tags", "body", "rating", "faced_company", "evidence"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
            "tags": forms.SelectMultiple(attrs={"class": "select2-multiple"}),
            "existing_company": forms.Select(attrs={"class": "select2-single"}),
            "faced_company": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Refresh company list
        self.fields["existing_company"].queryset = Company.objects.all()
        # Add select2 class for searchable dropdown
        self.fields["existing_company"].widget.attrs.update({"class": "select2-single"})
        self.fields["new_company_country"].widget.attrs.update({"class": "select2-single"})
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "Company",
                "existing_company",
                HTML("<hr>"),
                HTML("<h5>Or create new company:</h5>"),
                Row(Column("new_company_name"), Column("new_company_country")),
                Row(Column("new_company_city"), Column("new_company_industry")),
                "new_company_address",
                "new_company_website",
            ),
            Fieldset(
                "Review",
                Row(Column("title"), Column("rating")),
                "faced_company",
                "tags",
                "body",
                "evidence",
            ),
            Submit("submit", "Submit Review"),
        )

    def clean(self):
        cleaned_data = super().clean()
        existing_company = cleaned_data.get("existing_company")
        new_company_name = cleaned_data.get("new_company_name")
        new_company_country = cleaned_data.get("new_company_country")

        # Check that either existing company is selected OR new company info is provided
        if not existing_company and not (new_company_name and new_company_country):
            raise forms.ValidationError(
                "Please either select an existing company or provide information for a new company."
            )

        if existing_company and new_company_name:
            raise forms.ValidationError(
                "Please either select an existing company OR create a new one, not both."
            )

        return cleaned_data

    def _post_clean(self):
        # Skip ModelForm's _post_clean to avoid validation errors for non-model fields
        pass

    def save(self, commit=True):
        # Get or create the company
        existing_company = self.cleaned_data.get("existing_company")

        if existing_company:
            company = existing_company
        else:
            # Create new company
            company_data = {
                "name": self.cleaned_data.get("new_company_name"),
                "country": self.cleaned_data.get("new_company_country"),
                "city": self.cleaned_data.get("new_company_city") or "",
                "address": self.cleaned_data.get("new_company_address") or "",
                "website": self.cleaned_data.get("new_company_website") or "",
                "industry": self.cleaned_data.get("new_company_industry") or "",
            }
            company, created = Company.objects.get_or_create_from_data(company_data)

        # Use self.instance to save with proper user
        self.instance.company = company
        self.instance.title = self.cleaned_data.get("title")
        self.instance.body = self.cleaned_data.get("body")
        self.instance.rating = self.cleaned_data.get("rating")
        self.instance.faced_company = self.cleaned_data.get("faced_company")
        self.instance.evidence = self.cleaned_data.get("evidence")

        if commit:
            self.instance.save()
            # Set tags after saving (ManyToMany requires saved instance)
            tags = self.cleaned_data.get("tags")
            if tags:
                self.instance.tags.set(tags)

        return self.instance


class CommentForm(forms.ModelForm):
    """Form for adding comments to a review."""

    parent_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Comment
        fields = ["message", "tag", "photos"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3, "placeholder": "Write your comment..."}),
            "tag": forms.Select(attrs={"class": "select2-single"}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("review", None)  # Remove review if passed
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "parent_id",
            "message",
            "tag",
            "photos",
            Submit("submit", "Post Comment", css_class="btn-primary")
        )


class ReviewUpdateForm(forms.ModelForm):
    """Form for adding an update to a review."""

    disable_comments = forms.BooleanField(
        required=False,
        initial=False,
        label="Disable comments on this review",
        help_text="Check to prevent new comments on this review"
    )

    class Meta:
        model = ReviewUpdate
        fields = ["message", "tags", "photos"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Share an update about your experience..."}),
            "tags": forms.SelectMultiple(attrs={"class": "select2-multiple"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "message",
            "tags",
            "photos",
            "disable_comments",
            Submit("submit", "Post Update", css_class="btn-primary")
        )


class ReviewAdminForm(forms.ModelForm):
    """Form for admin review management."""

    class Meta:
        model = Review
        fields = ["status", "thumbnail"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "status",
            "thumbnail",
            Submit("submit", "Update Review"),
        )
