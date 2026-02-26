from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms

from apps.users.models import User
from apps.companies.forms import CompanyForm
from apps.companies.forms import CompanyForm


class UserCreationForm(forms.ModelForm):
    """Form for user registration with phone and full name."""

    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ["full_name", "phone", "email", "country"]

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Form for editing user profile."""

    class Meta:
        model = User
        fields = ["full_name", "email", "country", "phone", "avatar", "bio"]


def register_view(request):
    """User registration view."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("review_list")
    else:
        form = UserCreationForm()

    return render(request, "users/register.html", {"form": form})


@login_required
def profile_view(request):
    """User profile view."""
    return render(request, "users/profile.html", {"user": request.user})


@login_required
def profile_edit_view(request):
    """Edit user profile. For company accounts, also edit company info."""
    # Check if user has a claimed company
    claimed_company = getattr(request.user, "claimed_company", None)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        company_form = CompanyForm(request.POST, instance=claimed_company) if claimed_company else None

        if form.is_valid():
            form.save()

        company_form_valid = company_form.is_valid() if company_form else True
        if company_form and not company_form_valid:
            # Re-render with errors
            return render(request, "users/profile_edit.html", {
                "form": form,
                "company_form": company_form,
                "claimed_company": claimed_company
            })

        if company_form and company_form_valid:
            company_form.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
        company_form = CompanyForm(instance=claimed_company) if claimed_company else None

    return render(request, "users/profile_edit.html", {
        "form": form,
        "company_form": company_form,
        "claimed_company": claimed_company
    })
