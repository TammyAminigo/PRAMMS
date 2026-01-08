from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import LandlordRegistrationForm, CustomLoginForm
from .models import User


class HomeView(TemplateView):
    """Landing page for the application."""
    template_name = 'home.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)


class LandlordRegisterView(CreateView):
    """Registration view for Landlords only."""
    model = User
    form_class = LandlordRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, f'Welcome, {self.object.first_name}! Your landlord account has been created.')
        return response


def login_choice(request):
    """Login role selection page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/login_choice.html')


def landlord_login(request):
    """Landlord-specific login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_landlord:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('landlord_dashboard')
            else:
                messages.error(request, 'This account is not registered as a landlord. Please use the tenant login.')
                return redirect('tenant_login')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/landlord_login.html', {'form': form})


def tenant_login(request):
    """Tenant-specific login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_tenant:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('tenant_dashboard')
            else:
                messages.error(request, 'This account is not registered as a tenant. Please use the landlord login.')
                return redirect('landlord_login')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/tenant_login.html', {'form': form})


class CustomLogoutView(LogoutView):
    """Logout view."""
    next_page = 'home'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)


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
    """Landlord dashboard showing properties and maintenance requests."""
    if not request.user.is_landlord:
        messages.error(request, 'Access denied. Landlord account required.')
        return redirect('dashboard')
    
    properties = request.user.properties.all()
    
    # Get all maintenance requests for landlord's properties
    from maintenance.models import MaintenanceRequest
    maintenance_requests = MaintenanceRequest.objects.filter(
        property__landlord=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'properties': properties,
        'properties_count': properties.count(),
        'occupied_count': properties.filter(is_occupied=True).count(),
        'vacant_count': properties.filter(is_occupied=False).count(),
        'maintenance_requests': maintenance_requests,
        'pending_requests': MaintenanceRequest.objects.filter(
            property__landlord=request.user,
            status='pending'
        ).count(),
    }
    return render(request, 'accounts/landlord_dashboard.html', context)


@login_required
def tenant_dashboard(request):
    """Tenant dashboard showing their property and maintenance requests."""
    if not request.user.is_tenant:
        messages.error(request, 'Access denied. Tenant account required.')
        return redirect('dashboard')
    
    try:
        tenant_profile = request.user.tenant_profile
        property_info = tenant_profile.rental_property
    except:
        property_info = None
        tenant_profile = None
    
    # Get tenant's maintenance requests
    from maintenance.models import MaintenanceRequest
    maintenance_requests = MaintenanceRequest.objects.filter(
        tenant=request.user
    ).order_by('-created_at')
    
    context = {
        'tenant_profile': tenant_profile,
        'property': property_info,
        'maintenance_requests': maintenance_requests,
    }
    return render(request, 'accounts/tenant_dashboard.html', context)


@login_required
def my_account(request):
    """User account page for profile management."""
    from .forms import ProfilePictureForm
    
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile picture updated successfully!')
            return redirect('my_account')
    else:
        form = ProfilePictureForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/my_account.html', context)

