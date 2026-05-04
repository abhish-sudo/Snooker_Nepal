from django import forms
from .models import Registration
from .models import Tournament


class RegistrationForm(forms.ModelForm):
    class Meta:
        model  = Registration
        fields = ['full_name', 'phone', 'city', 'age', 'club_or_hall', 'payment_screenshot']
        labels = {
            'full_name':          'Full Name',
            'phone':              'Mobile Number',
            'city':               'Your City',
            'age':                'Your Age',
            'club_or_hall':       'Club / Hall (optional)',
            'payment_screenshot': 'Payment Screenshot',
        }
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'e.g. Ram Bahadur Thapa',
                'autocomplete': 'name',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'e.g. 9841XXXXXX',
                'type': 'tel',
                'autocomplete': 'tel',
                'maxlength': '15',
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'e.g. Kathmandu',
            }),
            'age': forms.NumberInput(attrs={
                'placeholder': 'e.g. 24',
                'min': '10',
                'max': '80',
            }),
            'club_or_hall': forms.TextInput(attrs={
                'placeholder': 'e.g. City Snooker Club',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = phone.replace('+', '').replace('-', '').replace(' ', '')
        if not digits.isdigit():
            raise forms.ValidationError('Please enter a valid mobile number.')
        if len(digits) < 10:
            raise forms.ValidationError('Mobile number must be at least 10 digits.')
        return phone

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and (age < 10 or age > 80):
            raise forms.ValidationError('Please enter a valid age between 10 and 80.')
        return age
    


class TournamentSubmitForm(forms.ModelForm):
    
    # Override date fields to make them not required at field level
    # clean() handles the required logic based on is_coming_soon
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'sub-input'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'sub-input'})
    )
    registration_deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'sub-input'})
    )

    class Meta:
        model  = Tournament
        fields = [
            'name', 'format', 'category', 'city', 'venue_name',
            'venue_map_link', 'is_coming_soon',
            'start_date', 'end_date',
            'registration_deadline', 'entry_fee', 'prize_money',
            'max_players', 'contact_phone', 'poster', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'venue_map_link': forms.URLInput(attrs={'placeholder': 'https://maps.google.com/...'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': 'e.g. 9841XXXXXX'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Kathmandu Open 2025'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Kathmandu'}),
            'venue_name': forms.TextInput(attrs={'placeholder': 'e.g. City Snooker Club'}),
        }

    def clean(self):
        cleaned = super().clean()
        coming_soon = cleaned.get('is_coming_soon')

        if not coming_soon:
            for field in ['start_date', 'end_date', 'registration_deadline']:
                if not cleaned.get(field):
                    self.add_error(field, 'This field is required unless marked as Coming Soon.')
        return cleaned