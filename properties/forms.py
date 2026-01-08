from django import forms
from .models import Property, InvitationLink


class PropertyForm(forms.ModelForm):
    """Form for adding/editing properties."""
    
    class Meta:
        model = Property
        fields = ['name', 'address', 'unit_number', 'rent_amount', 'rent_period']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Property name'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Full address',
                'rows': 3
            }),
            'unit_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Unit number (optional)'
            }),
            'rent_amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Rent amount in Naira (₦)',
                'step': '1'
            }),
            'rent_period': forms.Select(attrs={
                'class': 'form-input'
            }),
        }
        labels = {
            'rent_amount': 'Rent Amount (₦)',
            'rent_period': 'Rent Period',
        }


class InvitationForm(forms.ModelForm):
    """Form for generating tenant invitation links."""
    
    class Meta:
        model = InvitationLink
        fields = ['tenant_email']
        widgets = {
            'tenant_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Tenant email address'
            }),
        }
