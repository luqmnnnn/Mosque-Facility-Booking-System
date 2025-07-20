from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Booking, Facility,UserProfile
from django.utils import timezone

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True)
    ic_number = forms.CharField(label='IC Number', required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # Ensure UserProfile is created with extra fields
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': self.cleaned_data['phone'],
                    'ic_number': self.cleaned_data['ic_number'],
                    'role': 'Public'  # Set default role here
                }
            )
        return user
class BookingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['facility'].queryset = Facility.objects.filter(is_active=True)

    class Meta:
        model = Booking
        fields = ['facility', 'event_type', 'event_date', 'time_slot']
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date', 'min': (timezone.now() + timezone.timedelta(days=3)).date()}),
        }

    def clean_event_date(self):
        date = self.cleaned_data['event_date']
        min_date = timezone.now().date() + timezone.timedelta(days=3)
        if date < min_date:
            raise forms.ValidationError(f"You can only book events starting from {min_date}.")
        return date

    
from django import forms
from .models import UserProfile

class FullProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'ic_number', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].disabled = True  
        self.fields['role'].required = False  

