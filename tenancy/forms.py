from django import forms
from .models import TenancyApplication


class TenancyApplicationForm(forms.ModelForm):
    """Form for tenants to apply for a property."""
    
    move_in_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        }),
        help_text="Your preferred move-in date"
    )
    
    class Meta:
        model = TenancyApplication
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Tell the landlord why you are interested in this property...',
                'rows': 4
            }),
        }


class TerminationForm(forms.Form):
    """Form for confirming tenancy termination."""
    
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Reason for termination (optional)...',
            'rows': 3
        })
    )
    confirm = forms.BooleanField(
        required=True,
        label="I confirm I want to terminate this tenancy",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )
