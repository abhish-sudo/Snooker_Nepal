import re
from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    """
    Checkout form for creating orders.
    - Phone validation accepts Nepal (+977) and international formats
    - Placeholders replace verbose labels for a clean UI
    """

    class Meta:
        model = Order
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'address_line1',
            'address_line2',
            'city',
            'state_province',
            'postal_code',
            'country',
            'notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'First Name',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Last Name',
                'autocomplete': 'family-name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your@email.com',
                'autocomplete': 'email',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+977 98XXXXXXXX',
                'autocomplete': 'tel',
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Street Address',
                'autocomplete': 'address-line1',
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Apartment, suite, etc. (optional)',
                'autocomplete': 'address-line2',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'City',
                'autocomplete': 'address-level2',
            }),
            'state_province': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Province (e.g. Bagmati)',
                'autocomplete': 'address-level1',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Postal Code',
                'autocomplete': 'postal-code',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-input',
                'autocomplete': 'country-name',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Special instructions (optional)',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address_line2'].required = False
        self.fields['notes'].required         = False
        self.fields['country'].initial        = 'Nepal'
        # Placeholders serve as labels — hide verbose label text
        for field in self.fields.values():
            field.label = ''

    # ── Validation ──────────────────────────────────────────────────────

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()

        # Strip spaces and dashes for validation
        digits_only = re.sub(r'[\s\-]', '', phone)

        # Nepal mobile: 98XXXXXXXX or 97XXXXXXXX (10 digits)
        nepal_mobile = re.match(r'^(\+977|977|0)?[9][6-9]\d{8}$', digits_only)

        # Nepal landline: 01-XXXXXXX, 061-XXXXXX, etc.
        nepal_landline = re.match(r'^(\+977|977|0)?\d{7,10}$', digits_only)

        # Generic international: starts with + and 7–15 digits
        international = re.match(r'^\+\d{7,15}$', digits_only)

        if not (nepal_mobile or nepal_landline or international):
            raise forms.ValidationError(
                'Enter a valid phone number (e.g. +977 9800000000 or 01-4XXXXXX).'
            )

        return phone

    def clean_postal_code(self):
        code = self.cleaned_data.get('postal_code', '').strip()
        if code and not re.match(r'^\d{5}$', code):
            raise forms.ValidationError(
                'Nepal postal codes are 5 digits (e.g. 44600).'
            )
        return code

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('First name must be at least 2 characters.')
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters.')
        return name