from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from prmms.admin_site import propz_admin_site


class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone')}),
    )


# Register with custom admin site
propz_admin_site.register(User, UserAdmin)

