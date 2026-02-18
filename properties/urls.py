from django.urls import path
from . import views

urlpatterns = [
    # Public Marketplace
    path('marketplace/', views.marketplace_list, name='marketplace_list'),
    path('marketplace/<int:pk>/', views.marketplace_detail, name='marketplace_detail'),
    path('mortgage/', views.mortgage_info, name='mortgage_info'),
    path('features/marketplace/', views.feature_marketplace, name='feature_marketplace'),
    path('features/connections/', views.feature_connections, name='feature_connections'),
    path('features/lifecycle/', views.feature_lifecycle, name='feature_lifecycle'),
    path('features/maintenance/', views.feature_maintenance, name='feature_maintenance'),
    path('features/analytics/', views.feature_analytics, name='feature_analytics'),
    
    # Landlord Property Management
    path('', views.property_list, name='property_list'),
    path('add/', views.property_add, name='property_add'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('<int:pk>/delete/', views.property_delete, name='property_delete'),
]
