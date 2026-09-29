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
        for field_name, values, label in ((
            'profession', settings.occupation_options, 'Select occupation'),
            ('income_range', settings.income_ranges, 'Select income bracket'),
            ('family_type', settings.family_type_options, 'Select family type'),
            ('marital_status', settings.marital_status_options, 'Select marital status'),
        ):
            current = getattr(self.instance, field_name, '') if self.instance else ''
            options = list(values or [])
            if current and current not in options: options.append(current)
            self.fields[field_name].widget = forms.Select(choices=[('', label)] + [(v, v) for v in options])
        self.fields['languages'].help_text = 'Select/edit languages from Settings; use comma-separated values here for existing profiles.'
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
    preferred_locations = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':2, 'placeholder':'One location per line'}))
    preferred_cities = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':2, 'placeholder':'One city per line'}))
    preferred_education_options = forms.MultipleChoiceField(required=False)
    preferred_professions = forms.MultipleChoiceField(required=False)
    preferred_income_options = forms.MultipleChoiceField(required=False)
    preferred_marital_status_options = forms.MultipleChoiceField(required=False)
    preferred_languages = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings = FamilyHarmonySettings.current()
        multiple = {
            'preferred_education_options': settings.education_levels,
            'preferred_professions': settings.occupation_options,
            'preferred_income_options': settings.income_ranges,
            'preferred_marital_status_options': settings.marital_status_options,
            'preferred_languages': settings.language_options,
        }
        for name, values in multiple.items():
            choices=[(v, v) for v in (values or [])]
            self.fields[name].choices = choices
            self.fields[name].widget = forms.SelectMultiple(choices=choices, attrs={'size': '5'})
        self.fields['preferred_locations'].widget = forms.Textarea(attrs={'rows':2, 'placeholder':'One location per line'})
        self.fields['preferred_cities'].widget = forms.Textarea(attrs={'rows':2, 'placeholder':'One city per line'})

    def clean(self):
        cleaned = super().clean()
        for name in ('preferred_locations','preferred_cities'):
            value = self.data.get(name, '')
            if isinstance(value, str): cleaned[name] = [x.strip() for x in value.splitlines() if x.strip()]
        for name in ('preferred_education_options','preferred_professions','preferred_income_options','preferred_marital_status_options','preferred_languages'):
            cleaned[name] = self.data.getlist(name)
        return cleaned

    class Meta:
        model = FamilyHarmonyPreference
        exclude = ('profile', 'preferred_education', 'preferred_income', 'preferred_marital_status', 'preferred_regions')
        widgets = {'preferred_family_values': forms.Textarea(attrs={'rows': 2}), 'preferred_personality': forms.Textarea(attrs={'rows': 2}), 'other_expectations': forms.Textarea(attrs={'rows': 2}), 'free_text_seeking_description': forms.Textarea(attrs={'rows': 2})}
