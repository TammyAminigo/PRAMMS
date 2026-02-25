from django.urls import path
from . import views

urlpatterns = [
    path('apply/<int:property_pk>/', views.apply_for_property, name='apply_for_property'),
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<int:pk>/accept/', views.accept_application, name='accept_application'),
    path('applications/<int:pk>/reject/', views.reject_application, name='reject_application'),
    path('applications/<int:pk>/reply/', views.reply_to_application, name='reply_to_application'),
    path('<int:pk>/', views.tenancy_detail, name='tenancy_detail'),
    path('<int:pk>/terminate/', views.terminate_tenancy, name='terminate_tenancy'),
    path('active/', views.active_tenancies, name='active_tenancies'),
    path('history/', views.past_tenancies, name='past_tenancies'),
    path('<int:pk>/tenant-profile/', views.tenant_profile, name='tenant_profile'),
    path('<int:pk>/upload-document/', views.upload_tenant_document, name='upload_tenant_document'),
    path('document/<int:pk>/delete/', views.delete_tenant_document, name='delete_tenant_document'),
]
