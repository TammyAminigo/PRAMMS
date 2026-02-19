from django import forms
from .models import Property


class PropertyForm(forms.ModelForm):
    """Form for adding/editing properties — includes marketplace fields."""
    

    class Meta:
        model = Property
        fields = ['name', 'address', 'state', 'unit_number', 'description', 'property_type',
                  'listing_type', 'rent_amount', 'rent_period', 'bedrooms', 'is_available', 'photo',
                  'shortlet_start', 'shortlet_end']
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
            'shortlet_start': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
            'shortlet_end': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
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
            'shortlet_start': 'Check-in Date',
            'shortlet_end': 'Check-out Date',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # rent_period is not required for sale/land/shortlet listings
        self.fields['rent_period'].required = False
        self.fields['shortlet_start'].required = False
        self.fields['shortlet_end'].required = False

    def clean(self):
        cleaned_data = super().clean()
        listing_type = cleaned_data.get('listing_type')

        if listing_type == 'sale' or listing_type == 'land':
            # Sale/land listings don't need a rent period — set a sensible default
            if not cleaned_data.get('rent_period'):
                cleaned_data['rent_period'] = 12
        elif listing_type == 'shortlet':
            # Shortlet listings need start and end dates
            start = cleaned_data.get('shortlet_start')
            end = cleaned_data.get('shortlet_end')
            if start and end:
                if end <= start:
                    self.add_error('shortlet_end', 'Check-out date must be after check-in date.')
                from datetime import date
                if start < date.today():
                    self.add_error('shortlet_start', 'Check-in date cannot be in the past.')
            # Set a default rent period for shortlet
            if not cleaned_data.get('rent_period'):
                cleaned_data['rent_period'] = 1
        elif listing_type == 'rent':
            # Rent listings must have a rent period
            if not cleaned_data.get('rent_period'):
                self.add_error('rent_period', 'Rent period is required for rental listings.')

        return cleaned_data
