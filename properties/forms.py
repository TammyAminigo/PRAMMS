from django import forms
from .models import Property


class PropertyForm(forms.ModelForm):
    """Form for adding/editing properties — includes marketplace fields."""
    
    class Meta:
        model = Property
        fields = ['name', 'address', 'state', 'unit_number', 'description', 'property_type',
                  'listing_type', 'rent_amount', 'rent_period', 'bedrooms', 'is_available', 'photo']
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
            'state': forms.Select(attrs={
                'class': 'form-input'
            }),
            'unit_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Unit number (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Describe the property for potential buyers or tenants...',
                'rows': 4
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-input'
            }),
            'listing_type': forms.HiddenInput(),
            'rent_amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Amount in Naira (₦)',
                'step': '1'
            }),
            'rent_period': forms.Select(attrs={
                'class': 'form-input'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            }),
            'bedrooms': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Number of bedrooms',
                'min': '1',
                'max': '20'
            }),
        }
        labels = {
            'rent_amount': 'Price (₦)',
            'rent_period': 'Rent Period',
            'bedrooms': 'Bedrooms',
            'is_available': 'List on Marketplace',
            'listing_type': 'Listing Type',
            'property_type': 'Property Type',
            'state': 'State / Location',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # rent_period is not required for sale listings
        self.fields['rent_period'].required = False

    def clean(self):
        cleaned_data = super().clean()
        listing_type = cleaned_data.get('listing_type')

        if listing_type == 'sale':
            # Sale listings don't need a rent period — set a sensible default
            if not cleaned_data.get('rent_period'):
                cleaned_data['rent_period'] = 12
        elif listing_type in ('rent', 'shortlet'):
            # Rent/shortlet listings must have a rent period
            if not cleaned_data.get('rent_period'):
                self.add_error('rent_period', 'Rent period is required for rental listings.')

        return cleaned_data
