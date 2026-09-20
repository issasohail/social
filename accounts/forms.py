from django import forms
from django.contrib.auth.models import Group, User

from boards.models import Board
from organization.models import Jamatkhana, LocalCouncil, NationalCouncil, RegionalCouncil, UserJurisdictionAccess


class StaffUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
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
        return user


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
