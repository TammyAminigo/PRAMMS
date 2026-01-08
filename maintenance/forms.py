from django import forms
from .models import MaintenanceRequest, MaintenanceImage


class MaintenanceRequestForm(forms.ModelForm):
    """Form for creating maintenance requests."""
    
    class Meta:
        model = MaintenanceRequest
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Brief title of the issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Describe the maintenance issue in detail...',
                'rows': 5
            }),
            'priority': forms.Select(attrs={
                'class': 'form-input'
            }),
        }


class MaintenanceStatusForm(forms.ModelForm):
    """Form for updating maintenance request status (Landlord only)."""
    
    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'landlord_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-input'
            }),
            'landlord_notes': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Add notes about this maintenance request...',
                'rows': 3
            }),
        }
