from django import forms

from organization.models import Jamatkhana
from settings_app.models import FamilyHarmonySettings

from .models import Person


class PersonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = FamilyHarmonySettings.current()
        self.fields['title'].widget = forms.Select(choices=[('', 'Select title')] + [(v, v) for v in cfg.title_options])
        self.fields['gender'].widget = forms.Select(choices=[('', 'Select gender'), ('Male', 'Male'), ('Female', 'Female')])
        select_lists = [
            ('nationality', cfg.nationality_options), ('country', cfg.country_options),
            ('marital_status', cfg.marital_status_options), ('education', cfg.education_levels),
            ('occupation', cfg.occupation_options), ('employer_or_business', cfg.employer_options),
            ('income_range', cfg.income_ranges),
        ]
        for name, values in select_lists:
            self.fields[name].widget = forms.Select(choices=[('', 'Select')] + [(v, v) for v in (values or [])])
            self.fields[name].choices = [('', 'Select')] + [(v, v) for v in (values or [])]
        self.fields['languages'].widget = forms.TextInput(attrs={
            'list': 'person-languages-options', 'data-options': '|'.join(cfg.language_options or [])
        })
        self.fields['jamatkhana'].queryset = Jamatkhana.objects.select_related(
            'local_council__regional_council'
        ).filter(is_active=True).order_by('name')
        self.fields['jamatkhana'].label = 'Jamatkhana'
        self.fields['jamatkhana'].label_from_instance = lambda o: (
            f'{o.name} — {o.local_council.name} — {o.local_council.regional_council.name}'
        )
        self.fields['jamatkhana'].widget.attrs['data-searchable'] = 'true'
        for field_name in ('photo', 'cnic_front', 'cnic_back'):
            self.fields[field_name].widget.attrs['accept'] = 'image/*'
        self.fields['cnic_front'].label = 'CNIC front'
        self.fields['cnic_back'].label = 'CNIC back'

    def save(self, commit=True):
        person = super().save(commit=False)
        if person.jamatkhana_id:
            person.local_council = person.jamatkhana.local_council
            person.region = person.local_council.regional_council
        else:
            person.local_council = None
            person.region = None
        if commit:
            person.save()
            self.save_m2m()
        return person

    class Meta:
        model = Person
        exclude = (
            'full_name', 'normalized_identity_number', 'created_by', 'updated_by', 'created_at',
            'updated_at', 'archived_at', 'is_demo', 'region', 'local_council'
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'current_address': forms.Textarea(attrs={'rows': 2}),
            'permanent_address': forms.Textarea(attrs={'rows': 2}),
            'interests': forms.Textarea(attrs={'rows': 2}),
        }
