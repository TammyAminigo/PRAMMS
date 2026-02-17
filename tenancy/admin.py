from django.contrib import admin
from .models import Tenancy, TenancyApplication


@admin.register(TenancyApplication)
class TenancyApplicationAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'rental_property', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['tenant__username', 'tenant__email', 'rental_property__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Tenancy)
class TenancyAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'landlord', 'rental_property', 'status', 'start_date', 'created_at']
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['tenant__username', 'landlord__username', 'rental_property__name']
    readonly_fields = ['created_at', 'updated_at', 'terminated_at']

