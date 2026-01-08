from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import Property, TenantProfile, InvitationLink
from .forms import PropertyForm, InvitationForm
from accounts.forms import TenantRegistrationForm


@login_required
def property_list(request):
    """List all properties for the logged-in landlord."""
    if not request.user.is_landlord:
        messages.error(request, 'Access denied. Landlord account required.')
        return redirect('dashboard')
    
    properties = request.user.properties.all()
    return render(request, 'properties/property_list.html', {'properties': properties})


@login_required
def property_add(request):
    """Add a new property."""
    if not request.user.is_landlord:
        messages.error(request, 'Access denied. Landlord account required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.landlord = request.user
            property_obj.save()
            messages.success(request, f'Property "{property_obj.name}" added successfully!')
            return redirect('property_list')
    else:
        form = PropertyForm()
    
    return render(request, 'properties/property_form.html', {
        'form': form,
        'title': 'Add Property'
    })


@login_required
def property_detail(request, pk):
    """View property details."""
    property_obj = get_object_or_404(Property, pk=pk)
    
    # Only allow landlord to view their own properties
    if property_obj.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('property_list')
    
    # Get active invitation links
    invitations = property_obj.invitations.filter(is_used=False)
    
    context = {
        'property': property_obj,
        'invitations': invitations,
    }
    return render(request, 'properties/property_detail.html', context)


@login_required
def property_edit(request, pk):
    """Edit a property."""
    property_obj = get_object_or_404(Property, pk=pk)
    
    if property_obj.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('property_list')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('property_detail', pk=pk)
    else:
        form = PropertyForm(instance=property_obj)
    
    return render(request, 'properties/property_form.html', {
        'form': form,
        'title': 'Edit Property',
        'property': property_obj
    })


@login_required
def property_delete(request, pk):
    """Delete a property."""
    property_obj = get_object_or_404(Property, pk=pk)
    
    if property_obj.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('property_list')
    
    if request.method == 'POST':
        name = property_obj.name
        property_obj.delete()
        messages.success(request, f'Property "{name}" deleted successfully.')
        return redirect('property_list')
    
    return render(request, 'properties/property_confirm_delete.html', {
        'property': property_obj
    })


@login_required
def generate_invitation(request, pk):
    """Generate a tenant invitation link for a property."""
    property_obj = get_object_or_404(Property, pk=pk)
    
    if property_obj.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('property_list')
    
    if property_obj.is_occupied:
        messages.warning(request, 'This property already has a tenant.')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.landlord = request.user
            invitation.rental_property = property_obj
            invitation.expires_at = timezone.now() + timedelta(days=7)
            invitation.save()
            
            invite_url = invitation.get_invite_url(request)
            messages.success(
                request, 
                f'Invitation link created! Share this link with your tenant: {invite_url}'
            )
            return redirect('property_detail', pk=pk)
    else:
        form = InvitationForm()
    
    return render(request, 'properties/generate_invitation.html', {
        'form': form,
        'property': property_obj
    })


def accept_invitation(request, token):
    """Accept an invitation and register as a tenant."""
    invitation = get_object_or_404(InvitationLink, token=token)
    
    # Check if invitation is valid
    if not invitation.is_valid_invite():
        messages.error(request, 'This invitation link has expired or already been used.')
        return redirect('home')
    
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            # Create the tenant user
            user = form.save()
            
            # Create tenant profile
            TenantProfile.objects.create(
                user=user,
                landlord=invitation.landlord,
                rental_property=invitation.rental_property,
                move_in_date=form.cleaned_data['move_in_date']
            )
            
            # Mark property as occupied and invitation as used
            invitation.rental_property.is_occupied = True
            invitation.rental_property.save()
            invitation.is_used = True
            invitation.save()
            
            # Log the user in
            from django.contrib.auth import login
            login(request, user)
            
            messages.success(
                request, 
                f'Welcome, {user.first_name}! Your tenant account has been created.'
            )
            return redirect('tenant_dashboard')
    else:
        initial_data = {}
        if invitation.tenant_email:
            initial_data['email'] = invitation.tenant_email
        form = TenantRegistrationForm(initial=initial_data)
    
    return render(request, 'properties/accept_invitation.html', {
        'form': form,
        'invitation': invitation,
        'property': invitation.rental_property
    })


@login_required
def tenant_delete(request, pk):
    """Delete a tenant from a property (Landlord only)."""
    tenant_profile = get_object_or_404(TenantProfile, pk=pk)
    
    # Only the landlord of this tenant can delete
    if tenant_profile.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('property_list')
    
    property_obj = tenant_profile.rental_property
    tenant_user = tenant_profile.user
    tenant_name = tenant_user.get_full_name() or tenant_user.username
    
    if request.method == 'POST':
        # Delete tenant user (cascades to profile and maintenance requests)
        tenant_user.delete()
        
        # Mark property as vacant
        property_obj.is_occupied = False
        property_obj.save()
        
        messages.success(request, f'Tenant "{tenant_name}" has been removed from {property_obj.name}.')
        return redirect('property_detail', pk=property_obj.pk)
    
    return render(request, 'properties/tenant_confirm_delete.html', {
        'tenant_profile': tenant_profile,
        'property': property_obj
    })


@login_required
def invitation_delete(request, pk):
    """Delete/cancel a pending invitation (Landlord only)."""
    invitation = get_object_or_404(InvitationLink, pk=pk)
    
    # Only the landlord who created the invitation can delete it
    if invitation.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('property_list')
    
    property_pk = invitation.rental_property.pk
    
    if request.method == 'POST':
        invitation.delete()
        messages.success(request, 'Invitation cancelled successfully.')
        return redirect('property_detail', pk=property_pk)
    
    # For GET requests, just redirect back (use POST form in template)
    return redirect('property_detail', pk=property_pk)
