"""Company forms using crispy forms."""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Field, Row, Column, Div, Submit, HTML, Hidden, Div

from .models import Company, CompanyClaim
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import CountryField
from apps.users.models import User


class CompanyChoiceField(forms.ModelChoiceField):
    """Custom choice field for company selection."""

    def label_from_instance(self, obj):
        return f"{obj.name} ({obj.country})"


class CompanyForm(forms.ModelForm):
    """Form for editing company information."""

    class Meta:
        model = Company
        fields = [
            'name',
            'country',
            'city',
            'address',
            'phone',
            'website',
            'industry'
        ]
        widgets = {
            'country': CountrySelectWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Company Information',
                'name',
                Row(
                    Column('country', css_class='col-md-6'),
                    Column('city', css_class='col-md-6'),
                ),
                'address',
                Row(
                    Column('phone', css_class='col-md-6'),
                    Column('website', css_class='col-md-6'),
                ),
                'industry',
            ),
        )


class ClaimRequestForm(forms.Form):
    """Form for claiming an existing company."""

    existing_company = CompanyChoiceField(
        queryset=Company.objects.filter(claimed_by__isnull=True),
        required=True,
        help_text="Select the company you want to claim"
    )

    verification_method = forms.ChoiceField(
        choices=CompanyClaim.VerificationMethod.choices,
        required=True
    )
    verification_email = forms.EmailField(
        required=False,
        help_text="Company email for verification"
    )
    verification_document = forms.FileField(
        required=False,
        help_text="Upload business registration or authorization document"
    )
    verification_website_code = forms.CharField(
        max_length=100,
        required=False,
        help_text="Verification code placed on company website"
    )
    requester_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Your name"
    )
    requester_role = forms.CharField(
        max_length=100,
        required=False,
        help_text="Your role at the company"
    )
    requester_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Additional information supporting the claim"
    )

    def __init__(self, *args, **kwargs):
        self.hide_company_field = kwargs.pop('hide_company_field', False)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'

        # Build layout based on whether company field should be hidden
        if self.hide_company_field:
            # When company is pre-selected, don't include the field in the form
            # The view will set it manually
            self.helper.layout = Layout(
                Fieldset(
                    "Verification",
                    'verification_method',
                    'verification_email',
                    'verification_document',
                    'verification_website_code',
                ),
                Fieldset(
                    "Your Information",
                    'requester_name',
                    'requester_role',
                    'requester_notes'
                ),
                Submit('submit', 'Submit Claim Request')
            )
        else:
            self.helper.layout = Layout(
                Fieldset(
                    "Select Company",
                    'existing_company'
                ),
                Fieldset(
                    "Verification",
                    'verification_method',
                    'verification_email',
                    'verification_document',
                    'verification_website_code',
                ),
                Fieldset(
                    "Your Information",
                    'requester_name',
                    'requester_role',
                    'requester_notes'
                ),
                Submit('submit', 'Submit Claim Request')
            )

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('verification_method')

        if method == CompanyClaim.VerificationMethod.EMAIL:
            if not cleaned_data.get('verification_email'):
                self.add_error('verification_email', 'Email is required for email verification')

        elif method == CompanyClaim.VerificationMethod.DOCUMENTS:
            if not cleaned_data.get('verification_document'):
                self.add_error('verification_document', 'Document is required for document verification')

        elif method == CompanyClaim.VerificationMethod.WEBSITE:
            if not cleaned_data.get('verification_website_code'):
                self.add_error('verification_website_code', 'Website code is required for website verification')

        return cleaned_data

    def save(self, user, commit=True):
        from . import services
        claim = services.claim_request_create(
            user=user,
            company=self.cleaned_data['existing_company'],
            verification_method=self.cleaned_data['verification_method'],
            verification_email=self.cleaned_data.get('verification_email', ''),
            verification_document=self.cleaned_data.get('verification_document'),
            verification_website_code=self.cleaned_data.get('verification_website_code', ''),
            requester_name=self.cleaned_data.get('requester_name', ''),
            requester_role=self.cleaned_data.get('requester_role', ''),
            requester_notes=self.cleaned_data.get('requester_notes', '')
        )
        return claim


class NewCompanyWithClaimForm(forms.ModelForm):
    """Form for creating a new company and claiming it with account creation."""

    # User account fields
    full_name = forms.CharField(max_length=150, label="Your Full Name")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(max_length=20, label="Your Phone Number")
    user_country = CountryField().formfield(label="Your Country", widget=CountrySelectWidget())
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    company_phone = forms.CharField(max_length=20, label="Company Phone", required=False)

    # Company phone (separate from user phone)
    company_phone = forms.CharField(max_length=20, label="Company Phone", required=False)

    class Meta:
        model = Company
        fields = [
            'name',
            'country',
            'city',
            'address',
            'website',
            'industry'
        ]
        widgets = {
            'country': CountrySelectWidget(),
        }

    # Verification fields (not part of Company model)
    verification_method = forms.ChoiceField(
        choices=CompanyClaim.VerificationMethod.choices,
        required=True
    )
    verification_email = forms.EmailField(
        required=False,
        help_text="Company email for verification"
    )
    verification_document = forms.FileField(
        required=False,
        help_text="Upload business registration or authorization document"
    )
    verification_website_code = forms.CharField(
        max_length=100,
        required=False,
        help_text="Verification code placed on company website"
    )
    requester_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Your name"
    )
    requester_role = forms.CharField(
        max_length=100,
        required=False,
        help_text="Your role at the company"
    )
    requester_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Additional information supporting the claim"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.form_class = 'row'
        self.helper.layout = Layout(
            Row(
                Column(
                    Fieldset(
                        "Account Information",
                        'full_name',
                        'email',
                        'phone',
                        'user_country',
                        'password1',
                        'password2',
                    ),
                    css_class="col-md-6"
                ),
                Column(
                    Fieldset(
                        "Company Information",
                        'name',
                        Row(
                            Column('country'),
                            Column('city'),
                        ),
                        'address',
                        Row(
                            Column('company_phone'),
                            Column('website'),
                        ),
                        'industry'
                    ),
                    css_class="col-md-6"
                ),
            ),
            Fieldset(
                "Verification",
                'verification_method',
                'verification_email',
                'verification_document',
                'verification_website_code',
            ),
            Fieldset(
                "Your Role",
                'requester_role',
                'requester_notes'
            ),
            Submit('submit', 'Register & Submit Claim', css_class='mt-3')
        )

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('verification_method')

        # Password validation
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Passwords do not match')
            if len(password1) < 8:
                self.add_error('password1', 'Password must be at least 8 characters')

        # Email validation
        if not cleaned_data.get('email'):
            self.add_error('email', 'Email is required')

        if method == CompanyClaim.VerificationMethod.EMAIL:
            if not cleaned_data.get('verification_email'):
                self.add_error('verification_email', 'Email is required for email verification')

        elif method == CompanyClaim.VerificationMethod.DOCUMENTS:
            if not cleaned_data.get('verification_document'):
                self.add_error('verification_document', 'Document is required for document verification')

        elif method == CompanyClaim.VerificationMethod.WEBSITE:
            if not cleaned_data.get('verification_website_code'):
                self.add_error('verification_website_code', 'Website code is required for website verification')

        return cleaned_data


class CompanyResponseForm(forms.Form):
    """Form for company to respond to a review."""

    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your response...'}),
        required=True,
        help_text="Your response to this review"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'message',
            Submit('submit', 'Post Response')
        )

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError("Response must be at least 10 characters")
        if len(message) > 2000:
            raise forms.ValidationError("Response must not exceed 2000 characters")
        return message


class CompanyForm(forms.ModelForm):
    """Form for editing company information in profile."""

    class Meta:
        model = Company
        fields = [
            'name',
            'country',
            'city',
            'address',
            'phone',
            'website',
            'industry'
        ]
        widgets = {
            'country': CountrySelectWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Company Information',
                Row(
                    Column('name', css_class='col-12'),
                ),
                Row(
                    Column('country', css_class='col-md-6'),
                    Column('city', css_class='col-md-6'),
                ),
                'address',
                Row(
                    Column('phone', css_class='col-md-6'),
                    Column('website', css_class='col-md-6'),
                ),
                'industry',
            )
        )


class AdminClaimReviewForm(forms.ModelForm):
    """Form for admin to review a claim."""

    class Meta:
        model = CompanyClaim
        fields = ['admin_notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
