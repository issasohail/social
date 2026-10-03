from django import forms

from settings_app.models import FamilyHarmonySettings

from .models import FamilyHarmonyPreference, FamilyHarmonyProfile


def _datalist(field, list_id, values):
    field.widget = forms.TextInput(attrs={'list': list_id, 'data-options': '|'.join(values or [])})


def _select(field, values, placeholder, current_value=''):
    """Render configured profile lists as single-value selects.

    Preserve an older saved value even if Settings no longer contains it, so
    editing an existing profile does not fail validation.
    """
    choices = [('', placeholder)] + [(value, value) for value in (values or [])]
    current_value = (current_value or '').strip()
    if current_value and current_value not in {value for value, _label in choices}:
        choices.append((current_value, f'{current_value} (current saved value)'))
    field.choices = choices
    field.widget = forms.Select(choices=choices)


YES_NO_UNKNOWN = [('', 'Not specified'), ('true', 'Yes'), ('false', 'No')]


class FamilyHarmonyProfileForm(forms.ModelForm):
    height_feet = forms.IntegerField(required=False, min_value=3, max_value=8, label='Height (ft)')
    height_inches = forms.IntegerField(required=False, min_value=0, max_value=11, label='Height (in)')
    known_diseases = forms.MultipleChoiceField(required=False, label='Known disease(s)')
    disability_status = forms.MultipleChoiceField(required=False, label='Disability status')
    languages = forms.MultipleChoiceField(required=False, label='Languages')
    caste_tribe = forms.MultipleChoiceField(required=False, label='Caste / tribe')
    marital_status = forms.ChoiceField(required=False, label='Marital status')
    profession = forms.CharField(required=False, label='Profession')
    income_range = forms.ChoiceField(required=False, label='Income range')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = FamilyHarmonySettings.current()
        self.fields['status'].required = False
        self.fields['status'].initial = self.instance.status if self.instance and self.instance.pk else FamilyHarmonyProfile.Status.DRAFT
        for name, values, placeholder in [
            ('marital_status', cfg.marital_status_options, ''),
            ('education_level', cfg.education_levels, ''),
            ('family_type', cfg.family_type_options, ''),
            ('income_range', cfg.income_ranges, ''),
        ]:
            current_value = getattr(self.instance, name, '') if self.instance and self.instance.pk else ''
            if name in {'marital_status', 'income_range'} and current_value:
                current_value = current_value.split(',')[0].strip()
            _select(self.fields[name], values, placeholder, current_value=current_value)
        for name, values in [
            ('languages', cfg.language_options), ('caste_tribe', cfg.caste_tribe_options),
        ]:
            choices = [(value, value) for value in (values or [])]
            self.fields[name].choices = choices
            self.fields[name].widget = forms.CheckboxSelectMultiple(choices=choices)
        self.fields['profession'].widget = forms.TextInput(attrs={'list': 'profession-options', 'placeholder': 'Select or type a profession'})
        self.fields['physical_status'].widget = forms.Select(
            choices=[('', '')] + [(v, v) for v in cfg.physical_status_options]
        )
        disability_choices = [(v, v) for v in cfg.disability_options]
        self.fields['disability_status'].choices = disability_choices
        self.fields['disability_status'].widget = forms.CheckboxSelectMultiple(choices=disability_choices)
        disease_choices = [(v, v) for v in cfg.known_disease_options]
        self.fields['known_diseases'].choices = disease_choices
        self.fields['known_diseases'].widget = forms.CheckboxSelectMultiple(choices=disease_choices)
        self.fields['smoking'].widget = forms.Select(choices=[('', 'Select smoking status'), ('No', 'No'), ('Yes', 'Yes')])
        self.fields['owns_house'].widget = forms.Select(choices=[('', 'Select house ownership'), ('true', 'Yes'), ('false', 'No')])
        self.fields['owns_car'].widget = forms.Select(choices=[('', 'Select car ownership'), ('true', 'Yes'), ('false', 'No')])
        self.fields['weight_kg'].widget.attrs.update({'min': '20', 'max': '300', 'step': '0.1', 'placeholder': 'Optional'})
        self.fields['brothers_count'].widget.attrs.update({'min': '0', 'max': '30', 'placeholder': '0'})
        self.fields['sisters_count'].widget.attrs.update({'min': '0', 'max': '30', 'placeholder': '0'})
        if self.instance and self.instance.pk:
            self.initial['known_diseases'] = self.instance.known_diseases or []
            self.initial['disability_status'] = [value.strip() for value in (self.instance.disability_status or '').split(',') if value.strip()]
            self.initial['languages'] = [value.strip() for value in (self.instance.languages or '').split(',') if value.strip()]
            self.initial['caste_tribe'] = [value.strip() for value in (self.instance.caste_tribe or '').split(',') if value.strip()]
            self.initial['marital_status'] = (self.instance.marital_status or '').split(',')[0].strip()
            self.initial['income_range'] = (self.instance.income_range or '').split(',')[0].strip()
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
        obj.disability_status = ', '.join(self.cleaned_data.get('disability_status') or [])
        obj.languages = ', '.join(self.cleaned_data.get('languages') or [])
        obj.caste_tribe = ', '.join(self.cleaned_data.get('caste_tribe') or [])
        obj.marital_status = self.cleaned_data.get('marital_status') or ''
        obj.profession = (self.cleaned_data.get('profession') or '').strip()
        obj.income_range = self.cleaned_data.get('income_range') or ''
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
    preferred_income_options = forms.ChoiceField(required=False, label='Income')
    preferred_marital_status_options = forms.MultipleChoiceField(required=False)
    preferred_languages = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = FamilyHarmonySettings.current()
        mapping = {
            'preferred_education_options': cfg.education_levels,
            'preferred_professions': cfg.occupation_options,
            'preferred_marital_status_options': cfg.marital_status_options,
            'preferred_languages': cfg.language_options,
        }
        for name, values in mapping.items():
            choices = [('Any', 'Any')] + [(v, v) for v in (values or []) if v != 'Any']
            self.fields[name].choices = choices
            self.fields[name].widget = forms.CheckboxSelectMultiple(choices=choices)

        current_income = ''
        if self.instance and self.instance.pk:
            existing_income = self.instance.preferred_income_options or []
            if isinstance(existing_income, list) and existing_income:
                current_income = existing_income[0]
            elif isinstance(existing_income, str):
                current_income = existing_income
        income_choices = [('', 'Any')] + [(v, v) for v in (cfg.income_ranges or [])]
        if current_income and current_income not in {value for value, _label in income_choices}:
            income_choices.append((current_income, f'{current_income} (current saved value)'))
        self.fields['preferred_income_options'].choices = income_choices
        self.fields['preferred_income_options'].widget = forms.Select(choices=income_choices)
        if current_income:
            self.initial['preferred_income_options'] = current_income
        for name in ('minimum_age', 'maximum_age'):
            self.fields[name].widget = forms.Select(choices=[('', 'Any')] + [(i, str(i)) for i in range(18, 81)])
        self.fields['willingness_to_relocate'].widget = forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')])
        self.fields['preferred_family_type'].widget = forms.Select(choices=[('', 'Any')] + [(v, v) for v in (cfg.family_type_options or [])])
        self.fields['preferred_caste_tribe'].widget = forms.Select(choices=[('', 'Any')] + [(v, v) for v in (cfg.caste_tribe_options or [])])
        self.fields['preferred_country'].widget = forms.Select(choices=[('', 'Any')] + [(v, v) for v in (cfg.country_options or [])])

    def clean(self):
        cleaned = super().clean()
        for name in ('preferred_locations', 'preferred_cities'):
            value = (self.data.get(name) or '').strip()
            cleaned[name] = [x.strip() for x in value.replace('\n', ',').split(',') if x.strip()]
        for name in (
            'preferred_education_options', 'preferred_professions',
            'preferred_marital_status_options', 'preferred_languages'
        ):
            values = self.data.getlist(name)
            cleaned[name] = ['Any'] if 'Any' in values else values
        income = (self.data.get('preferred_income_options') or '').strip()
        cleaned['preferred_income_options'] = [income] if income else []
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        income = self.cleaned_data.get('preferred_income_options') or []
        if isinstance(income, str):
            income = [income] if income else []
        obj.preferred_income_options = income[:1]
        if commit:
            obj.save()
        return obj

    class Meta:
        model = FamilyHarmonyPreference
        exclude = ('profile', 'preferred_education', 'preferred_income', 'preferred_marital_status', 'preferred_regions')
        widgets = {
            'preferred_family_values': forms.Textarea(attrs={'rows': 2}),
            'preferred_personality': forms.Textarea(attrs={'rows': 2}),
            'other_expectations': forms.Textarea(attrs={'rows': 2}),
            'free_text_seeking_description': forms.Textarea(attrs={'rows': 2}),
        }
