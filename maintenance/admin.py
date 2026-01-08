from django.contrib import admin
from .models import MaintenanceRequest, MaintenanceImage
from prmms.admin_site import pramms_admin_site


class MaintenanceImageInline(admin.TabularInline):
    model = MaintenanceImage
    extra = 0
    max_num = 3


class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'tenant', 'property', 'priority', 'status', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'tenant__username', 'property__name']
    ordering = ['-created_at']
    inlines = [MaintenanceImageInline]


class MaintenanceImageAdmin(admin.ModelAdmin):
    list_display = ['request', 'image', 'uploaded_at']
    list_filter = ['uploaded_at']


# Register with custom admin site
pramms_admin_site.register(MaintenanceRequest, MaintenanceRequestAdmin)
pramms_admin_site.register(MaintenanceImage, MaintenanceImageAdmin)

