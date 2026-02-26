"""Company URL configuration."""
from django.urls import path
from . import views

urlpatterns = [
    # Company account views
    path('claim/', views.company_claim_request_view, name='company_claim'),
    path('claim/<uuid:company_id>/', views.company_claim_request_view, name='company_claim_with_company'),
    path('register/', views.company_register_and_claim_view, name='company_register'),
    path('dashboard/', views.company_dashboard_view, name='company_dashboard'),

    # Admin views for claim management
    path('admin/claims/', views.admin_claim_list_view, name='admin_claim_list'),
    path('admin/claims/<uuid:claim_id>/', views.admin_claim_detail_view, name='admin_claim_detail'),
    path('admin/claims/<uuid:claim_id>/approve/', views.admin_claim_approve_view, name='admin_claim_approve'),
    path('admin/claims/<uuid:claim_id>/reject/', views.admin_claim_reject_view, name='admin_claim_reject'),
]
