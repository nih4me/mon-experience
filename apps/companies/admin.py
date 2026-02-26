from django.contrib import admin
from apps.companies.models import Company, CompanyClaim


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "city", "industry", "is_verified", "created_at"]
    list_filter = ["country", "industry", "is_verified"]
    search_fields = ["name", "city", "industry"]
    ordering = ["name"]
    readonly_fields = ["verified_at", "claimed_by"]


@admin.register(CompanyClaim)
class CompanyClaimAdmin(admin.ModelAdmin):
    list_display = ["company", "user", "status", "verification_method", "created_at"]
    list_filter = ["status", "verification_method"]
    search_fields = ["company__name", "user__full_name", "user__phone"]
    ordering = ["-created_at"]
    readonly_fields = ["user", "company", "verification_method", "verification_email",
                      "verification_document", "verification_website_code", "requester_name",
                      "requester_role", "requester_notes", "created_at", "updated_at"]

    fieldsets = (
        ("Claim Information", {
            "fields": ("user", "company", "status")
        }),
        ("Verification Details", {
            "fields": ("verification_method", "verification_email", "verification_document",
                       "verification_website_code")
        }),
        ("Requester Information", {
            "fields": ("requester_name", "requester_role", "requester_notes")
        }),
        ("Admin Review", {
            "fields": ("reviewed_by", "reviewed_at", "rejection_reason", "admin_notes")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    actions = ["approve_claims", "reject_claims"]

    def approve_claims(self, request, queryset):
        from apps.companies import services
        approved_count = 0
        for claim in queryset.filter(status=CompanyClaim.Status.PENDING):
            try:
                services.claim_approve(claim, request.user)
                approved_count += 1
            except ValueError:
                pass
        self.message_user(request, f"{approved_count} claims approved.")

    def reject_claims(self, request, queryset):
        from apps.companies import services
        rejected_count = 0
        for claim in queryset.filter(status=CompanyClaim.Status.PENDING):
            try:
                services.claim_reject(claim, request.user, "Bulk rejection")
                rejected_count += 1
            except ValueError:
                pass
        self.message_user(request, f"{rejected_count} claims rejected.")
