from django.urls import path
from . import views

urlpatterns = [
    path('', views.maintenance_list, name='maintenance_list'),
    path('new/', views.maintenance_create, name='maintenance_create'),
    path('<int:pk>/', views.maintenance_detail, name='maintenance_detail'),
    path('<int:pk>/edit/', views.maintenance_edit, name='maintenance_edit'),
    path('<int:pk>/update-status/', views.maintenance_update_status, name='maintenance_update_status'),
    path('images/<int:pk>/delete/', views.maintenance_delete_image, name='maintenance_delete_image'),
]

