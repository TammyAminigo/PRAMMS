import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Property(models.Model):
    """Property owned by a Landlord."""
    
    RENT_PERIOD_CHOICES = [
        (1, '1 Month'),
        (2, '2 Months'),
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '1 Year'),
    ]
    
    LISTING_TYPE_CHOICES = [
        ('rent', 'For Rent'),
        ('sale', 'For Sale'),
        ('shortlet', 'Shortlet'),
        ('land', 'Land'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('flat', 'Flat'),
        ('shop', 'Shop/Commercial'),
        ('land', 'Land'),
        ('other', 'Other'),
    ]
    
    NIGERIAN_STATE_CHOICES = [
        ('abia', 'Abia'),
        ('adamawa', 'Adamawa'),
        ('akwa_ibom', 'Akwa Ibom'),
        ('anambra', 'Anambra'),
        ('bauchi', 'Bauchi'),
        ('bayelsa', 'Bayelsa'),
        ('benue', 'Benue'),
        ('borno', 'Borno'),
        ('cross_river', 'Cross River'),
        ('delta', 'Delta'),
        ('ebonyi', 'Ebonyi'),
        ('edo', 'Edo'),
        ('ekiti', 'Ekiti'),
        ('enugu', 'Enugu'),
        ('abuja', 'Abuja (FCT)'),
        ('gombe', 'Gombe'),
        ('imo', 'Imo'),
        ('jigawa', 'Jigawa'),
        ('kaduna', 'Kaduna'),
        ('kano', 'Kano'),
        ('katsina', 'Katsina'),
        ('kebbi', 'Kebbi'),
        ('kogi', 'Kogi'),
        ('kwara', 'Kwara'),
        ('lagos', 'Lagos'),
        ('nasarawa', 'Nasarawa'),
        ('niger', 'Niger'),
        ('ogun', 'Ogun'),
        ('ondo', 'Ondo'),
        ('osun', 'Osun'),
        ('oyo', 'Oyo'),
        ('plateau', 'Plateau'),
        ('rivers', 'Rivers'),
        ('sokoto', 'Sokoto'),
        ('taraba', 'Taraba'),
        ('yobe', 'Yobe'),
        ('zamfara', 'Zamfara'),
    ]
    
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='properties'
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    state = models.CharField(
        max_length=20,
        choices=NIGERIAN_STATE_CHOICES,
        default='abuja',
        help_text="State where the property is located"
    )
    unit_number = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True, help_text="Detailed description for marketplace listing")
    property_type = models.CharField(
        max_length=20,
        choices=PROPERTY_TYPE_CHOICES,
        default='house'
    )
    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPE_CHOICES,
        default='rent'
    )
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2)
    rent_period = models.IntegerField(
        choices=RENT_PERIOD_CHOICES,
        default=12,
        help_text="Rent payment period in months"
    )
    is_occupied = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True, help_text="Visible on public marketplace")
    photo = models.ImageField(upload_to='properties/', blank=True, null=True, help_text="Property photo")
    bedrooms = models.PositiveIntegerField(null=True, blank=True, help_text="Number of bedrooms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'properties'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.address}"
    
    def formatted_rent(self):
        """Return rent formatted in Naira."""
        return f"₦{self.rent_amount:,.0f}"
    
    def rent_period_display(self):
        """Return human-readable rent period."""
        return dict(self.RENT_PERIOD_CHOICES).get(self.rent_period, f"{self.rent_period} Months")


class TenantProfile(models.Model):
    """Profile linking a Tenant user to their Landlord and Property."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_profile'
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenants'
    )
    rental_property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name='tenant'
    )
    move_in_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenant_profiles'
    
    def __str__(self):
        return f"{self.user.username} @ {self.rental_property.name}"
    
    @property
    def lease_end_date(self):
        """Calculate lease end date based on move-in date and rent period."""
        from dateutil.relativedelta import relativedelta
        if self.move_in_date and self.rental_property:
            months = self.rental_property.rent_period
            return self.move_in_date + relativedelta(months=months)
        return None


class InvitationLink(models.Model):
    """Single-use invitation link for tenant registration."""
    
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    rental_property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tenant_email = models.EmailField(blank=True, help_text="Email of the tenant being invited")
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'invitation_links'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Default expiration: 7 days from creation
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Invite for {self.rental_property.name} - {self.token}"
    
    def is_valid_invite(self):
        """Check if the invitation link is still valid."""
        return not self.is_used and timezone.now() < self.expires_at
    
    def get_invite_url(self, request=None):
        """Generate the full invitation URL."""
        from django.urls import reverse
        path = reverse('accept_invitation', kwargs={'token': str(self.token)})
        if request:
            return request.build_absolute_uri(path)
        return path
