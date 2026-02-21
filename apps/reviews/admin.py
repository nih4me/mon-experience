from django.contrib import admin

from apps.reviews.models import Tag, Review, Comment


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "mood", "created_at"]
    list_filter = ["mood"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["mood", "name"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "company", "rating", "status", "is_hidden", "created_at"]
    list_filter = ["status", "rating", "created_at", "tags"]
    search_fields = ["title", "body", "user__username", "company__name"]
    readonly_fields = ["created_at", "updated_at"]
    fields = ["user", "company", "tags", "title", "body", "rating", "status", "is_hidden", "evidence", "thumbnail", "created_at", "updated_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["user", "review", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["message", "user__username", "review__title"]
    readonly_fields = ["created_at", "updated_at"]
