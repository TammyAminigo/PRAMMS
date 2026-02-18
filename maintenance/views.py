from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import MaintenanceRequest, MaintenanceImage
from .forms import MaintenanceRequestForm, MaintenanceStatusForm


@login_required
def maintenance_list(request):
    """List maintenance requests based on user role."""
    if request.user.is_landlord:
        # Landlords see requests for all their properties
        requests = MaintenanceRequest.objects.filter(
            property__landlord=request.user
        ).order_by('-created_at')
    elif request.user.is_tenant:
        # Tenants see only their own requests
        requests = MaintenanceRequest.objects.filter(
            tenant=request.user
        ).order_by('-created_at')
    else:
        requests = MaintenanceRequest.objects.none()
    
    return render(request, 'maintenance/maintenance_list.html', {
        'maintenance_requests': requests
    })


@login_required
def maintenance_create(request):
    """Create a new maintenance request (Tenant only)."""
    if not request.user.is_tenant:
        messages.error(request, 'Only tenants can create maintenance requests.')
        return redirect('dashboard')
    
    # Check for active tenancy
    from tenancy.models import Tenancy
    active_tenancy = Tenancy.objects.filter(
        tenant=request.user,
        status='active'
    ).first()
    
    if not active_tenancy:
        messages.error(request, 'You must have an active tenancy to create maintenance requests.')
        return redirect('tenant_dashboard')
    
    property_obj = active_tenancy.rental_property
    
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            maintenance_request = form.save(commit=False)
            maintenance_request.tenant = request.user
            maintenance_request.property = property_obj
            maintenance_request.save()
            
            # Handle image uploads (1-3 images)
            images = request.FILES.getlist('images')
            if len(images) > 3:
                messages.warning(request, 'Maximum 3 images allowed. Only first 3 were saved.')
                images = images[:3]
            
            for image in images:
                MaintenanceImage.objects.create(
                    request=maintenance_request,
                    image=image
                )
            
            messages.success(request, 'Maintenance request submitted successfully!')
            return redirect('maintenance_detail', pk=maintenance_request.pk)
    else:
        form = MaintenanceRequestForm()
    
    return render(request, 'maintenance/maintenance_form.html', {
        'form': form,
        'property': property_obj
    })


@login_required
def maintenance_detail(request, pk):
    """View maintenance request details."""
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    
    # Check access permission
    is_landlord = request.user == maintenance_request.property.landlord
    is_tenant = request.user == maintenance_request.tenant
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    status_form = None
    if is_landlord:
        status_form = MaintenanceStatusForm(instance=maintenance_request)
        # Mark as viewed by landlord
        if not maintenance_request.viewed_by_landlord:
            maintenance_request.viewed_by_landlord = True
            maintenance_request.save(update_fields=['viewed_by_landlord'])
    
    return render(request, 'maintenance/maintenance_detail.html', {
        'maintenance_request': maintenance_request,
        'is_landlord': is_landlord,
        'status_form': status_form
    })


@login_required
def maintenance_update_status(request, pk):
    """Update maintenance request status (Landlord only)."""
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    
    if request.user != maintenance_request.property.landlord:
        messages.error(request, 'Only the property landlord can update the status.')
        return redirect('maintenance_detail', pk=pk)
    
    if request.method == 'POST':
        form = MaintenanceStatusForm(request.POST, instance=maintenance_request)
        if form.is_valid():
            updated_request = form.save(commit=False)
            if updated_request.status == 'completed' and not maintenance_request.completed_at:
                updated_request.completed_at = timezone.now()
            updated_request.save()
            messages.success(request, 'Status updated successfully!')
    
    return redirect('maintenance_detail', pk=pk)


@login_required
def maintenance_edit(request, pk):
    """Edit a maintenance request (Tenant only, while status allows)."""
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    
    # Only the tenant who created the request can edit
    if request.user != maintenance_request.tenant:
        messages.error(request, 'You can only edit your own maintenance requests.')
        return redirect('maintenance_detail', pk=pk)
    
    # Only allow editing if status is pending or in_progress
    if maintenance_request.status not in ['pending', 'in_progress']:
        messages.error(request, 'This request can no longer be edited.')
        return redirect('maintenance_detail', pk=pk)
    
    current_images = maintenance_request.images.all()
    
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, instance=maintenance_request)
        if form.is_valid():
            form.save()
            
            # Handle new image uploads (limit to 3 total)
            new_images = request.FILES.getlist('images')
            current_count = current_images.count()
            available_slots = 3 - current_count
            
            if new_images:
                if len(new_images) > available_slots:
                    messages.warning(request, f'Maximum 3 images allowed. Only {available_slots} slots available.')
                    new_images = new_images[:available_slots]
                
                for image in new_images:
                    MaintenanceImage.objects.create(
                        request=maintenance_request,
                        image=image
                    )
            
            messages.success(request, 'Maintenance request updated successfully!')
            return redirect('maintenance_detail', pk=pk)
    else:
        form = MaintenanceRequestForm(instance=maintenance_request)
    
    return render(request, 'maintenance/maintenance_edit.html', {
        'form': form,
        'maintenance_request': maintenance_request,
        'current_images': current_images,
        'available_slots': 3 - current_images.count()
    })


@login_required
def maintenance_delete_image(request, pk):
    """Delete an image from a maintenance request (Tenant only)."""
    image = get_object_or_404(MaintenanceImage, pk=pk)
    maintenance_request = image.request
    
    # Only the tenant who created the request can delete images
    if request.user != maintenance_request.tenant:
        messages.error(request, 'You can only delete images from your own requests.')
        return redirect('maintenance_detail', pk=maintenance_request.pk)
    
    # Only allow deletion if status is pending or in_progress
    if maintenance_request.status not in ['pending', 'in_progress']:
        messages.error(request, 'Images can no longer be deleted from this request.')
        return redirect('maintenance_detail', pk=maintenance_request.pk)
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted successfully!')
        return redirect('maintenance_edit', pk=maintenance_request.pk)
    
    return redirect('maintenance_edit', pk=maintenance_request.pk)

