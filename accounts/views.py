from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import UnifiedRegistrationForm, CustomLoginForm, ProfilePictureForm, ContactSettingsForm
from .models import User


class HomeView(TemplateView):
    """Landing page for the application."""
    template_name = 'home.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)


# =============================================
# Unified Registration Flow
# =============================================

def unified_register(request):
    """Step 1: Single registration form for all users."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Preserve ?next= parameter through the flow
    next_url = request.GET.get('next', '')
    
    if request.method == 'POST':
        form = UnifiedRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Store next_url in session for choose_role to use
            if next_url:
                request.session['registration_next'] = next_url
            elif request.POST.get('next'):
                request.session['registration_next'] = request.POST.get('next')
            return redirect('choose_role')
    else:
        form = UnifiedRegistrationForm()
    
    return render(request, 'accounts/register.html', {
        'form': form,
        'next': next_url,
    })


@login_required
def choose_role(request):
    """Step 2: Role selection with visual cards."""
    user = request.user
    next_url = request.session.pop('registration_next', '')
    
    if request.method == 'POST':
        role = request.POST.get('role', 'tenant')
        if role in ('landlord', 'tenant'):
            user.role = role
            user.save()
        
        if role == 'landlord':
            messages.success(
                request,
                f'Welcome, {user.first_name}! Let\'s get your first property listed for the market.'
            )
            # If they came from "Post Property", send them to add property
            if next_url:
                return redirect(next_url)
            return redirect('landlord_dashboard')
        else:
            messages.success(
                request,
                f'Welcome to Propz, {user.first_name}! Start your search for verified properties here.'
            )
            return redirect('marketplace_list')
    
    return render(request, 'accounts/choose_role.html', {
        'next': next_url,
    })


# =============================================
# Unified Login
# =============================================

def unified_login(request):
    """Single login page for all roles."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    next_url = request.GET.get('next', '')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect to ?next= if provided
            post_next = request.POST.get('next', '')
            if post_next:
                return redirect(post_next)
            
            # Otherwise redirect based on role
            return redirect('dashboard')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url,
    })


# =============================================
# Legacy Login Views (backward compatibility)
# =============================================

def login_choice(request):
    """Login role selection page — now redirects to unified login."""
    return redirect('login')


def landlord_login(request):
    """Landlord-specific login — now redirects to unified login."""
    return redirect('login')


def tenant_login(request):
    """Tenant-specific login — now redirects to unified login."""
    return redirect('login')


# =============================================
# Logout
# =============================================

class CustomLogoutView(LogoutView):
    """Logout view."""
    next_page = 'home'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)


# =============================================
# Dashboard Routing
# =============================================

@login_required
def dashboard_view(request):
    """Role-based dashboard redirect."""
    user = request.user
    
    if user.is_landlord:
        return redirect('landlord_dashboard')
    elif user.is_tenant:
        return redirect('tenant_dashboard')
    elif user.is_admin_user:
        return redirect('admin:index')
    else:
        return redirect('home')


@login_required
def landlord_dashboard(request):
    """Landlord dashboard showing properties, tenancies, and applications."""
    user = request.user
    if not user.is_landlord:
        messages.error(request, 'Access denied. Landlord account required.')
        return redirect('dashboard')
    
    from properties.models import Property
    from tenancy.models import Tenancy, TenancyApplication
    from maintenance.models import MaintenanceRequest
    
    properties = Property.objects.filter(landlord=user)
    properties_count = properties.count()
    occupied_count = properties.filter(is_available=False).count()
    vacant_count = properties.filter(is_available=True).count()
    
    # Pending maintenance requests
    pending_requests = MaintenanceRequest.objects.filter(
        property__landlord=user,
        status='pending'
    ).count()
    
    # Recent maintenance requests
    maintenance_requests = MaintenanceRequest.objects.filter(
        property__landlord=user,
    ).order_by('-created_at')[:5]
    
    # Active tenancies
    active_tenancies = Tenancy.objects.filter(
        rental_property__landlord=user,
        status='active'
    ).select_related('tenant', 'rental_property')[:3]
    
    # Pending applications
    pending_applications = TenancyApplication.objects.filter(
        rental_property__landlord=user,
        status='pending'
    ).select_related('tenant', 'rental_property').order_by('-created_at')
    pending_applications_count = pending_applications.count()
    
    context = {
        'properties_count': properties_count,
        'occupied_count': occupied_count,
        'vacant_count': vacant_count,
        'pending_requests': pending_requests,
        'maintenance_requests': maintenance_requests,
        'active_tenancies': active_tenancies,
        'pending_applications': pending_applications,
        'pending_applications_count': pending_applications_count,
    }
    return render(request, 'accounts/landlord_dashboard.html', context)


@login_required
def tenant_dashboard(request):
    """Tenant dashboard showing their tenancy, property, and maintenance requests."""
    user = request.user
    if not user.is_tenant:
        messages.error(request, 'Access denied. Tenant account required.')
        return redirect('dashboard')
    
    from tenancy.models import Tenancy, TenancyApplication
    from maintenance.models import MaintenanceRequest
    
    # Current tenancy
    current_tenancy = Tenancy.objects.filter(
        tenant=user,
        status='active'
    ).select_related('rental_property').first()
    
    # Pending applications
    pending_applications = TenancyApplication.objects.filter(
        tenant=user,
        status='pending'
    ).select_related('rental_property').order_by('-created_at')
    
    # Maintenance requests
    maintenance_requests = []
    if current_tenancy:
        maintenance_requests = MaintenanceRequest.objects.filter(
            tenant=user,
            property=current_tenancy.rental_property
        ).order_by('-created_at')[:5]
    
    # Past tenancies
    past_tenancies = Tenancy.objects.filter(
        tenant=user,
        status='terminated'
    ).select_related('rental_property').order_by('-end_date')[:3]
    
    context = {
        'active_tenancy': current_tenancy,
        'pending_applications': pending_applications,
        'maintenance_requests': maintenance_requests,
        'past_tenancies': past_tenancies,
    }
    return render(request, 'accounts/tenant_dashboard.html', context)


# =============================================
# My Account / Profile
# =============================================

@login_required
def my_account(request):
    """User account page for profile management."""
    user = request.user
    
    if request.method == 'POST':
        if 'update_picture' in request.POST:
            picture_form = ProfilePictureForm(request.POST, request.FILES, instance=user)
            if picture_form.is_valid():
                picture_form.save()
                messages.success(request, 'Profile picture updated successfully!')
                return redirect('my_account')
            contact_form = ContactSettingsForm(instance=user)
        elif 'update_contact' in request.POST:
            contact_form = ContactSettingsForm(request.POST, instance=user)
            if contact_form.is_valid():
                contact_form.save()
                messages.success(request, 'Contact settings updated successfully!')
                return redirect('my_account')
            picture_form = ProfilePictureForm(instance=user)
        else:
            picture_form = ProfilePictureForm(instance=user)
            contact_form = ContactSettingsForm(instance=user)
    else:
        picture_form = ProfilePictureForm(instance=user)
        contact_form = ContactSettingsForm(instance=user)
    
    return render(request, 'accounts/my_account.html', {
        'form': picture_form,
        'contact_form': contact_form,
    })
