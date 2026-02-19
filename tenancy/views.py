from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Tenancy, TenancyApplication
from .forms import TenancyApplicationForm, TerminationForm
from properties.models import Property


@login_required
def apply_for_property(request, property_pk):
    """Tenant applies/expresses interest in a property."""
    if not request.user.is_tenant:
        messages.error(request, 'Only tenants can apply for properties.')
        return redirect('marketplace_list')
    
    property_obj = get_object_or_404(Property, pk=property_pk, is_available=True)
    
    # Check if tenant already has an active tenancy
    active_tenancy = Tenancy.objects.filter(
        tenant=request.user,
        status='active'
    ).first()
    if active_tenancy:
        messages.warning(request, 'You already have an active tenancy. You must terminate it before applying for a new property.')
        return redirect('marketplace_detail', pk=property_pk)
    
    # Check for existing application
    existing = TenancyApplication.objects.filter(
        tenant=request.user,
        rental_property=property_obj,
        status='pending'
    ).first()
    if existing:
        messages.info(request, 'You have already applied for this property.')
        return redirect('marketplace_detail', pk=property_pk)
    
    if request.method == 'POST':
        form = TenancyApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.tenant = request.user
            application.rental_property = property_obj
            application.save()
            messages.success(request, 'Your application has been submitted! The landlord will review it.')
            return redirect('marketplace_detail', pk=property_pk)
    else:
        form = TenancyApplicationForm()
    
    return render(request, 'tenancy/apply.html', {
        'form': form,
        'property': property_obj
    })


@login_required
def applications_list(request):
    """Landlord views all incoming applications for their properties."""
    if not request.user.is_landlord:
        messages.error(request, 'Access denied. Landlord account required.')
        return redirect('dashboard')
    
    applications = TenancyApplication.objects.filter(
        rental_property__landlord=request.user
    ).select_related('tenant', 'rental_property').order_by('-created_at')
    
    pending_count = applications.filter(status='pending').count()
    
    return render(request, 'tenancy/applications_list.html', {
        'applications': applications,
        'pending_count': pending_count
    })


@login_required
def accept_application(request, pk):
    """Landlord accepts a tenant application — creates a Tenancy."""
    application = get_object_or_404(TenancyApplication, pk=pk)
    
    if application.rental_property.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('applications_list')
    
    if application.status != 'pending':
        messages.warning(request, 'This application has already been processed.')
        return redirect('applications_list')
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        if not start_date:
            messages.error(request, 'Please provide a start date for the tenancy.')
            return redirect('applications_list')
        
        # Create the tenancy
        tenancy = Tenancy.objects.create(
            tenant=application.tenant,
            landlord=request.user,
            rental_property=application.rental_property,
            application=application,
            start_date=start_date,
            status='active'
        )
        
        # Update property status
        application.rental_property.is_occupied = True
        application.rental_property.is_available = False
        application.rental_property.save()
        
        # Update application status
        application.status = 'accepted'
        application.save()
        
        # Reject other pending applications for this property
        TenancyApplication.objects.filter(
            rental_property=application.rental_property,
            status='pending'
        ).exclude(pk=pk).update(status='rejected')
        
        messages.success(
            request,
            f'Tenancy created! {application.tenant.get_full_name()} is now a tenant at {application.rental_property.name}.'
        )
        return redirect('tenancy_detail', pk=tenancy.pk)
    
    return render(request, 'tenancy/accept_application.html', {
        'application': application
    })


@login_required
def reject_application(request, pk):
    """Landlord rejects a tenant application."""
    application = get_object_or_404(TenancyApplication, pk=pk)
    
    if application.rental_property.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('applications_list')
    
    if request.method == 'POST':
        application.status = 'rejected'
        application.save()
        messages.success(request, f'Application from {application.tenant.get_full_name()} rejected.')
    
    return redirect('applications_list')


@login_required
def reply_to_application(request, pk):
    """Landlord replies to a tenant application."""
    application = get_object_or_404(TenancyApplication, pk=pk)
    
    if application.rental_property.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('applications_list')
    
    if request.method == 'POST':
        reply_text = request.POST.get('landlord_reply', '').strip()
        if reply_text:
            application.landlord_reply = reply_text
            application.save()
            messages.success(request, f'Reply sent to {application.tenant.get_full_name()}.')
        else:
            messages.warning(request, 'Reply cannot be empty.')
    
    return redirect('applications_list')


@login_required
def tenancy_detail(request, pk):
    """View tenancy details — accessible by both landlord and tenant."""
    tenancy = get_object_or_404(Tenancy, pk=pk)
    
    is_landlord = request.user == tenancy.landlord
    is_tenant = request.user == tenancy.tenant
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    from properties.models import PropertyImage
    additional_images = PropertyImage.objects.filter(property=tenancy.rental_property).order_by('order')

    return render(request, 'tenancy/tenancy_detail.html', {
        'tenancy': tenancy,
        'is_landlord': is_landlord,
        'is_tenant': is_tenant,
        'additional_images': additional_images,
    })


@login_required
def terminate_tenancy(request, pk):
    """Either party initiates or confirms tenancy termination."""
    tenancy = get_object_or_404(Tenancy, pk=pk)
    
    is_landlord = request.user == tenancy.landlord
    is_tenant = request.user == tenancy.tenant
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if tenancy.status in ['terminated', 'archived']:
        messages.info(request, 'This tenancy has already been terminated.')
        return redirect('tenancy_detail', pk=pk)
    
    if request.method == 'POST':
        form = TerminationForm(request.POST)
        if form.is_valid():
            if is_landlord:
                tenancy.landlord_terminated = True
            elif is_tenant:
                tenancy.tenant_terminated = True
            
            fully_terminated = tenancy.check_termination()
            
            if fully_terminated:
                messages.success(request, 'Tenancy has been fully terminated. The property is now available on the marketplace.')
            else:
                who = "landlord" if is_landlord else "tenant"
                other = "tenant" if is_landlord else "landlord"
                messages.info(request, f'Termination requested by {who}. Waiting for {other} to confirm.')
            
            return redirect('tenancy_detail', pk=pk)
    else:
        form = TerminationForm()
    
    return render(request, 'tenancy/terminate.html', {
        'tenancy': tenancy,
        'form': form,
        'is_landlord': is_landlord,
    })


@login_required
def active_tenancies(request):
    """View all active tenancies based on user role."""
    if request.user.is_landlord:
        tenancies = Tenancy.objects.filter(
            landlord=request.user,
            status__in=['active', 'pending_termination']
        ).select_related('tenant', 'rental_property')
    elif request.user.is_tenant:
        tenancies = Tenancy.objects.filter(
            tenant=request.user,
            status__in=['active', 'pending_termination']
        ).select_related('landlord', 'rental_property')
    else:
        tenancies = Tenancy.objects.none()
    
    return render(request, 'tenancy/active_tenancies.html', {
        'tenancies': tenancies
    })


@login_required
def past_tenancies(request):
    """View historical/archived tenancies."""
    if request.user.is_landlord:
        tenancies = Tenancy.objects.filter(
            landlord=request.user,
            status__in=['terminated', 'archived']
        ).select_related('tenant', 'rental_property')
    elif request.user.is_tenant:
        tenancies = Tenancy.objects.filter(
            tenant=request.user,
            status__in=['terminated', 'archived']
        ).select_related('landlord', 'rental_property')
    else:
        tenancies = Tenancy.objects.none()
    
    return render(request, 'tenancy/past_tenancies.html', {
        'tenancies': tenancies
    })
