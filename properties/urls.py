from django.urls import path
from . import views

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('add/', views.property_add, name='property_add'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('<int:pk>/delete/', views.property_delete, name='property_delete'),
    path('<int:pk>/invite/', views.generate_invitation, name='generate_invitation'),
    path('invite/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    path('tenant/<int:pk>/delete/', views.tenant_delete, name='tenant_delete'),
    path('invitation/<int:pk>/delete/', views.invitation_delete, name='invitation_delete'),
]
