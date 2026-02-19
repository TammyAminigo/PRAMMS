from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import Property, PropertyImage
from .forms import PropertyForm


# ----- MARKETPLACE (PUBLIC) -----

def marketplace_list(request):
    """Public marketplace listing - browse available properties."""
    properties = Property.objects.filter(is_available=True).order_by('-created_at')
    
    # Search
    query = request.GET.get('q', '')
    if query:
        # Search by name, address, description, and state
        from properties.models import Property as P
        state_matches = [key for key, label in P.NIGERIAN_STATE_CHOICES if query.lower() in label.lower()]
        q_filter = (
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(description__icontains=query)
        )
        if state_matches:
            q_filter = q_filter | Q(state__in=state_matches)
        properties = properties.filter(q_filter)
    
    # Filter by listing type
    listing_type = request.GET.get('listing_type', '')
    if listing_type:
        properties = properties.filter(listing_type=listing_type)
    
    # Filter by property type
    property_type = request.GET.get('property_type', '')
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    # Filter by bedrooms
    bedrooms = request.GET.get('bedrooms', '')
    if bedrooms:
        properties = properties.filter(bedrooms=bedrooms)
    
    # Filter by price range
    min_price = request.GET.get('min_price', '')
    if min_price:
        properties = properties.filter(rent_amount__gte=min_price)
    
    max_price = request.GET.get('max_price', '')
    if max_price:
        properties = properties.filter(rent_amount__lte=max_price)
    
    # Determine if a real search/filter was performed (listing_type alone doesn't count)
    has_searched = bool(query or property_type or bedrooms or min_price or max_price)
    
    # If no results and no active search, show suggested properties
    suggested_properties = None
    if not properties.exists() and not has_searched:
        suggested_properties = Property.objects.filter(
            is_available=True
        ).order_by('?')[:8]
    
    # Build display labels for breadcrumbs
    listing_type_map = dict(Property.LISTING_TYPE_CHOICES)
    property_type_map = dict(Property.PROPERTY_TYPE_CHOICES)
    listing_type_display = listing_type_map.get(listing_type, '')
    property_type_display = property_type_map.get(property_type, '')
    
    context = {
        'properties': properties,
        'query': query,
        'listing_type': listing_type,
        'property_type': property_type,
        'bedrooms': bedrooms,
        'min_price': min_price,
        'max_price': max_price,
        'listing_type_display': listing_type_display,
        'property_type_display': property_type_display,
        'listing_type_choices': Property.LISTING_TYPE_CHOICES,
        'property_type_choices': Property.PROPERTY_TYPE_CHOICES,
        'has_searched': has_searched,
        'suggested_properties': suggested_properties,
    }
    return render(request, 'properties/marketplace_list.html', context)


def marketplace_detail(request, pk):
    """Public property detail page with 'Apply' CTA."""
    property_obj = get_object_or_404(Property, pk=pk, is_available=True)
    additional_images = property_obj.additional_images.all()
    
    # Check if current user has already applied
    has_applied = False
    if request.user.is_authenticated and request.user.is_tenant:
        from tenancy.models import TenancyApplication
        has_applied = TenancyApplication.objects.filter(
            tenant=request.user,
            rental_property=property_obj,
            status='pending'
        ).exists()
    
    context = {
        'property': property_obj,
        'has_applied': has_applied,
        'additional_images': additional_images,
    }
    return render(request, 'properties/marketplace_detail.html', context)


# ----- PROPERTY MANAGEMENT (LANDLORD) -----

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
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.landlord = request.user
            property_obj.save()
            # Handle additional photos
            additional_files = request.FILES.getlist('additional_photos')
            for i, photo in enumerate(additional_files[:5]):
                PropertyImage.objects.create(
                    property=property_obj,
                    image=photo,
                    order=i
                )
            messages.success(request, f'Property "{property_obj.name}" added and listed on the marketplace!')
            return redirect('property_list')
    else:
        form = PropertyForm()
    
    return render(request, 'properties/property_form.html', {
        'form': form,
        'title': 'Add Property'
    })


@login_required
def property_detail(request, pk):
    """View property details (Landlord management view)."""
    property_obj = get_object_or_404(Property, pk=pk)
    
    # Only allow landlord to view their own properties
    if property_obj.landlord != request.user:
        messages.error(request, 'Access denied.')
        return redirect('property_list')
    
    # Get active tenancy for this property
    from tenancy.models import Tenancy, TenancyApplication
    active_tenancy = Tenancy.objects.filter(
        rental_property=property_obj,
        status__in=['active', 'pending_termination']
    ).select_related('tenant').first()
    
    # Get pending applications for this property
    pending_applications = TenancyApplication.objects.filter(
        rental_property=property_obj,
        status='pending'
    ).select_related('tenant')
    
    context = {
        'property': property_obj,
        'active_tenancy': active_tenancy,
        'pending_applications': pending_applications,
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
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            form.save()
            # Handle additional photos
            additional_files = request.FILES.getlist('additional_photos')
            if additional_files:
                existing_count = property_obj.additional_images.count()
                slots = 5 - existing_count
                for i, photo in enumerate(additional_files[:slots]):
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=photo,
                        order=existing_count + i
                    )
            messages.success(request, 'Property updated successfully!')
            return redirect('property_detail', pk=pk)
    else:
        form = PropertyForm(instance=property_obj)
    
    existing_images = property_obj.additional_images.all()
    return render(request, 'properties/property_form.html', {
        'form': form,
        'title': 'Edit Property',
        'property': property_obj,
        'existing_images': existing_images,
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


# ----- MORTGAGE INFORMATION (PUBLIC) -----

def mortgage_info(request):
    """Public page explaining mortgages and linking to FMBN."""
    return render(request, 'properties/mortgage_info.html')


# ----- FEATURE INFO PAGES (PUBLIC) -----

def feature_marketplace(request):
    """Public page explaining the open marketplace feature."""
    return render(request, 'properties/feature_marketplace.html')


def feature_connections(request):
    """Public page explaining transparent connections feature."""
    return render(request, 'properties/feature_connections.html')


def feature_lifecycle(request):
    """Public page explaining lifecycle management feature."""
    return render(request, 'properties/feature_lifecycle.html')


def feature_maintenance(request):
    """Public page explaining maintenance requests feature."""
    return render(request, 'properties/feature_maintenance.html')


def feature_analytics(request):
    """Public page explaining property analytics feature."""
    return render(request, 'properties/feature_analytics.html')
