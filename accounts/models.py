from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with role-based access control."""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='landlord')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, help_text="WhatsApp phone number")
    telegram_username = models.CharField(max_length=50, blank=True, help_text="Telegram username (without @)")
    show_phone = models.BooleanField(default=False, help_text="Allow others to see your full phone number")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_landlord(self):
        return self.role == 'landlord'
    
    @property
    def is_tenant(self):
        return self.role == 'tenant'
    
    @property
    def is_admin_user(self):
        return self.role == 'admin'
    
    @property
    def has_profile_picture(self):
        return bool(self.profile_picture and self.profile_picture.name)

