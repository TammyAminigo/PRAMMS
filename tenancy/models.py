from django.db import models
from django.conf import settings
from properties.models import Property


class TenancyApplication(models.Model):
    """Application from a tenant expressing interest in a property."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenancy_applications'
    )
    rental_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    message = models.TextField(
        blank=True,
        help_text="Message to the landlord expressing your interest"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    landlord_reply = models.TextField(
        blank=True,
        help_text="Landlord's reply to the tenant's application"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenancy_applications'
        ordering = ['-created_at']
        # Prevent duplicate applications
        unique_together = ['tenant', 'rental_property']
    
    def __str__(self):
        return f"{self.tenant.get_full_name()} → {self.rental_property.name} ({self.get_status_display()})"


class Tenancy(models.Model):
    """Active or historical tenancy linking a tenant to a property and landlord."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending_termination', 'Pending Termination'),
        ('terminated', 'Terminated'),
        ('archived', 'Archived'),
    ]
    
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenancies'
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='landlord_tenancies'
    )
    rental_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='tenancies'
    )
    application = models.OneToOneField(
        TenancyApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenancy'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='active'
    )
    landlord_terminated = models.BooleanField(
        default=False,
        help_text="Has the landlord requested termination?"
    )
    tenant_terminated = models.BooleanField(
        default=False,
        help_text="Has the tenant requested termination?"
    )
    terminated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenancies'
        verbose_name_plural = 'Tenancies'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant.get_full_name()} @ {self.rental_property.name} ({self.get_status_display()})"
    
    @property
    def lease_end_date(self):
        """Calculate lease end date based on start date and rent period."""
        from dateutil.relativedelta import relativedelta
        if self.start_date and self.rental_property:
            months = self.rental_property.rent_period
            return self.start_date + relativedelta(months=months)
        return None
    
    @property
    def days_remaining(self):
        """Calculate days remaining until lease end."""
        from django.utils import timezone
        end = self.lease_end_date
        if end:
            delta = end - timezone.now().date()
            return max(0, delta.days)
        return None
    
    def check_termination(self):
        """
        Check if both parties have terminated. If so, finalize.
        Returns True if tenancy was fully terminated.
        """
        from django.utils import timezone
        if self.landlord_terminated and self.tenant_terminated:
            self.status = 'terminated'
            self.terminated_at = timezone.now()
            # Free the property
            self.rental_property.is_occupied = False
            self.rental_property.is_available = True
            self.rental_property.save()
            self.save()
            return True
        elif self.landlord_terminated or self.tenant_terminated:
            self.status = 'pending_termination'
            self.save()
        return False
