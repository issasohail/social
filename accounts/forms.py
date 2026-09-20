from django import forms
from django.contrib.auth.models import Group, User

from boards.models import Board
from .models import UserProfile
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil, UserJurisdictionAccess


class StaffUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    phone_number = forms.CharField(required=False, label='WhatsApp phone number')
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'groups', 'is_active')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            self.save_m2m()
            UserProfile.objects.update_or_create(user=user, defaults={'phone_number': self.cleaned_data.get('phone_number', '')})
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('phone_number',)


class JurisdictionAccessForm(forms.ModelForm):
    class Meta:
        model = UserJurisdictionAccess
        fields = ('level', 'national_council', 'regional_council', 'local_council', 'jamatkhana', 'board', 'is_active', 'start_date', 'end_date')
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}), 'end_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['national_council'].queryset = NationalCouncil.objects.filter(is_active=True)
        self.fields['regional_council'].queryset = RegionalCouncil.objects.filter(is_active=True)
        self.fields['local_council'].queryset = LocalCouncil.objects.filter(is_active=True)
        self.fields['jamatkhana'].queryset = Jamatkhana.objects.filter(is_active=True)
        self.fields['board'].queryset = Board.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        level = cleaned.get('level')
        required = {
            UserJurisdictionAccess.Level.NATIONAL: 'national_council',
            UserJurisdictionAccess.Level.REGIONAL: 'regional_council',
            UserJurisdictionAccess.Level.LOCAL: 'local_council',
            UserJurisdictionAccess.Level.JK: 'jamatkhana',
        }
        field = required.get(level)
        if field and not cleaned.get(field):
            self.add_error(field, 'Select the council for this access level.')
        if level == UserJurisdictionAccess.Level.REGIONAL and cleaned.get('regional_council'):
            cleaned['national_council'] = cleaned['regional_council'].national_council
        elif level == UserJurisdictionAccess.Level.LOCAL and cleaned.get('local_council'):
            cleaned['regional_council'] = cleaned['local_council'].regional_council
            cleaned['national_council'] = cleaned['regional_council'].national_council
        elif level == UserJurisdictionAccess.Level.JK and cleaned.get('jamatkhana'):
            cleaned['local_council'] = cleaned['jamatkhana'].local_council
            cleaned['regional_council'] = cleaned['local_council'].regional_council
            cleaned['national_council'] = cleaned['regional_council'].national_council
        return cleaned
