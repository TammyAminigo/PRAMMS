from django.urls import path
from . import views

urlpatterns = [
    # Unified registration flow
    path('register/', views.unified_register, name='register'),
    path('register/choose-role/', views.choose_role, name='choose_role'),
    
    # Unified login
    path('login/', views.unified_login, name='login'),
    
    # Legacy login routes (redirect to unified)
    path('login/choice/', views.login_choice, name='login_choice'),
    path('login/landlord/', views.landlord_login, name='landlord_login'),
    path('login/tenant/', views.tenant_login, name='tenant_login'),
    
    # Legacy register route (redirect to unified)
    path('register/tenant/', views.unified_register, name='register_tenant'),
    
    # Logout
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Dashboards
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('dashboard/tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    
    # Account
    path('my-account/', views.my_account, name='my_account'),
]
