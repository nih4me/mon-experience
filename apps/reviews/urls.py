from django.urls import path
from apps.reviews import views

urlpatterns = [
    path("", views.ReviewListView.as_view(), name="review_list"),
    path("reviews/<uuid:pk>/", views.ReviewDetailView.as_view(), name="review_detail"),
    path("reviews/new/", views.review_create_view, name="review_create"),
    path("my-reviews/", views.my_reviews_view, name="my_reviews"),
    path("my-reviews/<uuid:pk>/toggle-hide/", views.toggle_hide_review, name="toggle_hide_review"),
    path("my-reviews/<uuid:pk>/toggle-comments/", views.toggle_comments, name="toggle_comments"),
    path("tag/<slug:tag_slug>/", views.ReviewListView.as_view(), name="review_list_by_tag"),
]
