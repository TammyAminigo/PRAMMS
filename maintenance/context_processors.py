"""Context processors for the maintenance app."""

from .models import MaintenanceRequest


def unread_maintenance_count(request):
    """Add unread maintenance request count to template context for landlords."""
    if request.user.is_authenticated and hasattr(request.user, 'is_landlord') and request.user.is_landlord:
        count = MaintenanceRequest.objects.filter(
            property__landlord=request.user,
            viewed_by_landlord=False
        ).count()
        return {'unread_maintenance_count': count}
    return {'unread_maintenance_count': 0}
