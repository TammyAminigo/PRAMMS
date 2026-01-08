from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.LandlordRegisterView.as_view(), name='register'),
    path('login/', views.login_choice, name='login'),
    path('login/landlord/', views.landlord_login, name='landlord_login'),
    path('login/tenant/', views.tenant_login, name='tenant_login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('dashboard/tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    path('my-account/', views.my_account, name='my_account'),
]

