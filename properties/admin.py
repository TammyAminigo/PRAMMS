from django.contrib import admin
from .models import Property, TenantProfile, InvitationLink, PropertyImage
from prmms.admin_site import propz_admin_site


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    max_num = 5


class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'landlord', 'address', 'state', 'rent_amount', 'is_occupied', 'created_at']
    list_filter = ['is_occupied', 'state', 'listing_type', 'created_at']
    search_fields = ['name', 'address', 'landlord__username']
    ordering = ['-created_at']
    inlines = [PropertyImageInline]


class TenantProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'landlord', 'rental_property', 'move_in_date', 'created_at']
    list_filter = ['move_in_date', 'created_at']
    search_fields = ['user__username', 'landlord__username', 'rental_property__name']


class InvitationLinkAdmin(admin.ModelAdmin):
    list_display = ['token', 'landlord', 'rental_property', 'tenant_email', 'is_used', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['tenant_email', 'landlord__username', 'rental_property__name']
    readonly_fields = ['token']


# Register with custom admin site
propz_admin_site.register(Property, PropertyAdmin)
propz_admin_site.register(TenantProfile, TenantProfileAdmin)
propz_admin_site.register(InvitationLink, InvitationLinkAdmin)

