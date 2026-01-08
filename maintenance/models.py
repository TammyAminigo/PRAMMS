from django.db import models
from django.conf import settings
from properties.models import Property


class MaintenanceRequest(models.Model):
    """Maintenance request submitted by a Tenant."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    ]
    
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='maintenance_requests'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='maintenance_requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    landlord_notes = models.TextField(blank=True, help_text="Notes from landlord")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    viewed_by_landlord = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'maintenance_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.property.name}"


class MaintenanceImage(models.Model):
    """Image attachment for a maintenance request (1-3 images allowed)."""
    
    request = models.ForeignKey(
        MaintenanceRequest,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='maintenance_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'maintenance_images'
    
    def __str__(self):
        return f"Image for {self.request.title}"
