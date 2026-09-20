from django import forms

from organization.models import Jamatkhana, LocalCouncil, RegionalCouncil
from settings_app.models import FamilyHarmonySettings
from .models import FamilyHarmonyPreference, FamilyHarmonyProfile


class FamilyHarmonyProfileForm(forms.ModelForm):
    education_level = forms.ChoiceField(required=False)
    education_level_other = forms.CharField(required=False, label='Custom education level')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings = FamilyHarmonySettings.current()
        portfolio_choices = [(value, value) for value in settings.portfolio_options or ['Family Harmony', 'Seniors', 'Portfolio 3', 'Portfolio 4', 'Portfolio 5', 'Portfolio 6']]
        self.fields['portfolio'].choices = portfolio_choices
        choices = [(value, value) for value in settings.education_levels or ['Metric', 'O Level', 'Bachelor', 'Master', 'PhD', 'Other']]
        self.fields['education_level'].choices = [('', 'Select education level')] + choices
        self.fields['owning_jamatkhana'].label = 'Current Jamatkhana'
        self.fields['owning_jamatkhana'].queryset = Jamatkhana.objects.select_related('local_council__regional_council').order_by('local_council__regional_council__name', 'local_council__name', 'name')
        self.fields['owning_local_council'].queryset = LocalCouncil.objects.select_related('regional_council').order_by('regional_council__name', 'name')
        self.fields['owning_region'].queryset = RegionalCouncil.objects.order_by('name')
        self.fields['owning_jamatkhana'].label_from_instance = lambda obj: f'{obj.name} ({obj.local_council.name} / {obj.local_council.regional_council.name})'
        if self.instance and self.instance.education_level and self.instance.education_level not in {value for value, _ in choices}:
            self.initial['education_level'] = 'Other'
            self.initial['education_level_other'] = self.instance.education_level

    def clean(self):
        cleaned = super().clean()
        selected_level = cleaned.get('education_level')
        custom_level = (cleaned.get('education_level_other') or '').strip()
        if selected_level == 'Other':
            cleaned['education_level'] = custom_level or selected_level
        return cleaned

    class Meta:
        model = FamilyHarmonyProfile
        exclude = ('person', 'assigned_officer', 'created_at', 'updated_at', 'is_demo', 'consent_reviewed')
        widgets = {'family_background': forms.Textarea(attrs={'rows': 2}), 'family_values': forms.Textarea(attrs={'rows': 2}), 'personality': forms.Textarea(attrs={'rows': 2}), 'health_information': forms.Textarea(attrs={'rows': 2}), 'personal_statement': forms.Textarea(attrs={'rows': 2}), 'expectations': forms.Textarea(attrs={'rows': 2}), 'notes': forms.Textarea(attrs={'rows': 2})}


class FamilyHarmonyPreferenceForm(forms.ModelForm):
    class Meta:
        model = FamilyHarmonyPreference
        exclude = ('profile',)
        widgets = {'preferred_family_values': forms.Textarea(attrs={'rows': 2}), 'preferred_personality': forms.Textarea(attrs={'rows': 2}), 'other_expectations': forms.Textarea(attrs={'rows': 2}), 'free_text_seeking_description': forms.Textarea(attrs={'rows': 2})}
