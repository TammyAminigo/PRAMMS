from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class UnifiedRegistrationForm(UserCreationForm):
    """Single registration form for all users. Role is assigned separately."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone number (optional)'
        })
    )
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # Role defaults to 'tenant' — updated in choose_role view
        user.role = 'tenant'
        if commit:
            user.save()
        return user


# Legacy forms kept for backward compatibility
class LandlordRegistrationForm(UserCreationForm):
    """Registration form for Landlords."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone number (optional)'
        })
    )
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'landlord'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class TenantRegistrationForm(UserCreationForm):
    """Public registration form for Tenants."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone number (optional)'
        })
    )
    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'tenant'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    """Custom login form with styled inputs - supports username or email."""
    
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )
    
    def clean_username(self):
        """Allow login with either username or email (case-insensitive)."""
        username_or_email = self.cleaned_data.get('username')
        
        # Check if input is an email (case-insensitive lookup)
        if '@' in username_or_email:
            try:
                user = User.objects.get(email__iexact=username_or_email)
                return user.username
            except User.DoesNotExist:
                pass
        else:
            # Username lookup (case-insensitive)
            try:
                user = User.objects.get(username__iexact=username_or_email)
                return user.username
            except User.DoesNotExist:
                pass
        
        return username_or_email


class ProfilePictureForm(forms.ModelForm):
    """Form for uploading profile picture."""
    
    class Meta:
        model = User
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*'
            })
        }
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            # Validate file size (max 5MB)
            if picture.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image file too large. Please upload an image smaller than 5MB.')
        return picture


class ContactSettingsForm(forms.ModelForm):
    """Form for managing contact info and privacy settings."""
    
    class Meta:
        model = User
        fields = ['phone', 'whatsapp_number', 'telegram_username', 'show_phone']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. 08012345678'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. 2348012345678'
            }),
            'telegram_username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. username (without @)'
            }),
            'show_phone': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
        labels = {
            'phone': 'Phone Number',
            'whatsapp_number': 'WhatsApp Number',
            'telegram_username': 'Telegram Username',
            'show_phone': 'Show full phone number to others',
        }
