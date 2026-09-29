from django import forms

from settings_app.models import FamilyHarmonySettings

from .models import FamilyHarmonyPreference, FamilyHarmonyProfile


def _datalist(field, list_id, values):
    field.widget = forms.TextInput(attrs={'list': list_id, 'data-options': '|'.join(values or [])})


YES_NO_UNKNOWN = [('', 'Not specified'), ('true', 'Yes'), ('false', 'No')]


class FamilyHarmonyProfileForm(forms.ModelForm):
    height_feet = forms.IntegerField(required=False, min_value=3, max_value=8, label='Height (ft)')
    height_inches = forms.IntegerField(required=False, min_value=0, max_value=11, label='Height (in)')
    known_diseases = forms.MultipleChoiceField(required=False, label='Known disease(s)')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = FamilyHarmonySettings.current()
        self.fields['status'].required = False
        self.fields['status'].initial = self.instance.status if self.instance and self.instance.pk else FamilyHarmonyProfile.Status.DRAFT
        for name, values in [
            ('education_level', cfg.education_levels), ('profession', cfg.occupation_options),
            ('income_range', cfg.income_ranges), ('family_type', cfg.family_type_options),
            ('marital_status', cfg.marital_status_options), ('caste_tribe', cfg.caste_tribe_options),
            ('languages', cfg.language_options),
        ]:
            _datalist(self.fields[name], f'{name}-options', values)
        self.fields['physical_status'].widget = forms.Select(
            choices=[('', 'Select physical status')] + [(v, v) for v in cfg.physical_status_options]
        )
        self.fields['disability_status'].widget = forms.Select(
            choices=[('', 'Select disability status')] + [(v, v) for v in cfg.disability_options]
        )
        disease_choices = [(v, v) for v in cfg.known_disease_options]
        self.fields['known_diseases'].choices = disease_choices
        self.fields['known_diseases'].widget = forms.CheckboxSelectMultiple(choices=disease_choices)
        self.fields['smoking'].widget = forms.RadioSelect(choices=[('No', 'No'), ('Yes', 'Yes')])
        self.fields['owns_house'].widget = forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')])
        self.fields['owns_car'].widget = forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')])
        self.fields['weight_kg'].widget.attrs.update({'min': '20', 'max': '300', 'step': '0.1'})
        if self.instance and self.instance.pk:
            self.initial['known_diseases'] = self.instance.known_diseases or []
        if self.instance and self.instance.height_cm:
            total = round(self.instance.height_cm / 2.54)
            self.initial['height_feet'] = total // 12
            self.initial['height_inches'] = total % 12

    def save(self, commit=True):
        obj = super().save(commit=False)
        ft = self.cleaned_data.get('height_feet')
        inch = self.cleaned_data.get('height_inches')
        if ft is not None:
            obj.height_cm = round((ft * 12 + (inch or 0)) * 2.54)
        elif not self.cleaned_data.get('height_inches'):
            obj.height_cm = None
        obj.known_diseases = self.cleaned_data.get('known_diseases') or []
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = FamilyHarmonyProfile
        exclude = (
            'person', 'assigned_officer', 'created_at', 'updated_at', 'is_demo', 'consent_reviewed',
            'height_cm', 'owning_region', 'owning_local_council', 'owning_jamatkhana'
        )
        widgets = {
            x: forms.Textarea(attrs={'rows': 2}) for x in (
                'family_background', 'family_values', 'personality', 'health_information',
                'personal_statement', 'expectations', 'notes', 'other_lifestyle_details',
                'child_details', 'previous_marriage_notes', 'disabilities'
            )
        }


class FamilyHarmonyPreferenceForm(forms.ModelForm):
    preferred_locations = forms.CharField(required=False)
    preferred_cities = forms.CharField(required=False)
    preferred_education_options = forms.MultipleChoiceField(required=False)
    preferred_professions = forms.MultipleChoiceField(required=False)
    preferred_income_options = forms.MultipleChoiceField(required=False)
    preferred_marital_status_options = forms.MultipleChoiceField(required=False)
    preferred_languages = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = FamilyHarmonySettings.current()
        mapping = {
            'preferred_education_options': cfg.education_levels,
            'preferred_professions': cfg.occupation_options,
            'preferred_income_options': cfg.income_ranges,
            'preferred_marital_status_options': cfg.marital_status_options,
            'preferred_languages': cfg.language_options,
        }
        for name, values in mapping.items():
            choices = [('Any', 'Any')] + [(v, v) for v in (values or []) if v != 'Any']
            self.fields[name].choices = choices
            self.fields[name].widget = forms.SelectMultiple(choices=choices, attrs={'size': '4'})
        for name in ('minimum_age', 'maximum_age'):
            self.fields[name].widget = forms.Select(choices=[('', 'Any')] + [(i, str(i)) for i in range(18, 81)])
        self.fields['willingness_to_relocate'].widget = forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')])

    def clean(self):
        cleaned = super().clean()
        for name in ('preferred_locations', 'preferred_cities'):
            value = (self.data.get(name) or '').strip()
            cleaned[name] = [x.strip() for x in value.replace('\n', ',').split(',') if x.strip()]
        for name in (
            'preferred_education_options', 'preferred_professions', 'preferred_income_options',
            'preferred_marital_status_options', 'preferred_languages'
        ):
            values = self.data.getlist(name)
            cleaned[name] = ['Any'] if 'Any' in values else values
        return cleaned

    class Meta:
        model = FamilyHarmonyPreference
        exclude = ('profile', 'preferred_education', 'preferred_income', 'preferred_marital_status', 'preferred_regions')
        widgets = {
            'preferred_family_values': forms.Textarea(attrs={'rows': 2}),
            'preferred_personality': forms.Textarea(attrs={'rows': 2}),
            'other_expectations': forms.Textarea(attrs={'rows': 2}),
            'free_text_seeking_description': forms.Textarea(attrs={'rows': 2}),
        }
