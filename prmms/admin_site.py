from django.contrib.admin import AdminSite
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from accounts.models import User


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    """Custom authentication form that accepts username or email."""
    
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocapitalize': 'none',
            'autocomplete': 'username',
        })
    )
    
    def clean_username(self):
        """Allow login with either username or email (case-insensitive)."""
        username_or_email = self.cleaned_data.get('username')
        
        # Check if input is an email (case-insensitive lookup)
        if '@' in username_or_email:
            try:
                user = User.objects.get(email__iexact=username_or_email)
                return user.username
            except User.DoesNotExist:
                pass
        else:
            # Username lookup (case-insensitive)
            try:
                user = User.objects.get(username__iexact=username_or_email)
                return user.username
            except User.DoesNotExist:
                pass
        
        return username_or_email


class PRAMMSAdminSite(AdminSite):
    """Custom admin site for PRAMMS with email login support."""
    
    site_header = 'PRAMMS Administration'
    site_title = 'PRAMMS Admin'
    index_title = 'Property Rental and Maintenance Management'
    login_form = EmailOrUsernameAuthenticationForm
    
    def login(self, request, extra_context=None):
        """Override login to use custom authentication form."""
        extra_context = extra_context or {}
        extra_context['title'] = 'Admin Login'
        return super().login(request, extra_context)


# Create custom admin site instance
pramms_admin_site = PRAMMSAdminSite(name='pramms_admin')
