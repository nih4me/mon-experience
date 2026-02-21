from django.contrib import admin
from apps.companies.models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "city", "industry", "created_at"]
    list_filter = ["country", "industry"]
    search_fields = ["name", "city", "industry"]
    ordering = ["name"]
